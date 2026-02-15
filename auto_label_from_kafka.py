"""
Automated Intent Training Data Builder

Uses correlation rules to automatically label incidents.
Consumes from Kafka and builds training dataset without manual labeling.

This is much faster than manual labeling and uses your existing correlation rules!
"""

import json
import sys
from datetime import datetime, timedelta
from collections import defaultdict
from kafka import KafkaConsumer
import pandas as pd

sys.path.insert(0, '..')
from correlation_engine.intent_predictor import IntentFeatureBuilder, FEATURE_ORDER
from correlation_engine.rules_config import CORRELATION_RULES
from correlation_engine.rule_engine import RuleEngine

# ============================================================
# CONFIG
# ============================================================

KAFKA_BOOTSTRAP = "localhost:9092"

TOPICS = [
    "camera-anomaly-scores",
    "network-anomaly-scores",
    "log-anomaly-scores",
    "file-anomaly-scores"
]

OUTPUT_PATH = "data/processed/intent_training_data.csv"
WINDOW_SIZE = 15  # minutes


# ============================================================
# Auto Labeling using Correlation Rules
# ============================================================

class AutoLabeler:
    
    def __init__(self):
        self.rule_engine = RuleEngine()
        
    def label_incident(self, window):
        """
        Use correlation rules to automatically determine attack type.
        Returns the intent_label from the matched rule.
        """
        rule, filtered_events = self.rule_engine.evaluate(window)
        
        if rule:
            return rule.get('intent_label', 'unknown')
        return None


# ============================================================
# Data Collection
# ============================================================

def collect_and_label(duration_minutes=10, min_samples_per_class=100):
    """
    Collect data from Kafka and auto-label using correlation rules.
    
    Args:
        duration_minutes: How long to collect
        min_samples_per_class: Minimum samples needed per attack type
    """
    
    print("\n🎯 AUTO-LABELING FROM KAFKA")
    print(f"Duration: {duration_minutes} minutes")
    print(f"Target: {min_samples_per_class} samples per attack type\n")
    
    consumer = KafkaConsumer(
        *TOPICS,
        bootstrap_servers=KAFKA_BOOTSTRAP,
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        auto_offset_reset='earliest',  # Start from beginning
        enable_auto_commit=True,
        group_id='auto-intent-labeler'
    )
    
    events_by_zone = defaultdict(list)
    labeled_samples = defaultdict(list)
    labeler = AutoLabeler()
    
    start_time = datetime.now()
    event_count = 0
    
    print("📡 Collecting events from Kafka...\n")
    
    try:
        for message in consumer:
            event = message.value
            zone = event.get('zone', 'global')
            events_by_zone[zone].append(event)
            event_count += 1
            
            # Every 50 events, try to create windows and label
            if event_count % 50 == 0:
                new_samples = process_events(events_by_zone, labeler)
                for label, samples in new_samples.items():
                    labeled_samples[label].extend(samples)
                
                # Print progress
                elapsed = (datetime.now() - start_time).total_seconds() / 60
                total_labeled = sum(len(v) for v in labeled_samples.values())
                print(f"Events: {event_count} | Labeled incidents: {total_labeled} ({elapsed:.1f} min)")
                
                # Show distribution
                for label, samples in labeled_samples.items():
                    print(f"  {label}: {len(samples)}")
                print()
                
                # Check if we have enough samples
                if all(len(v) >= min_samples_per_class for v in labeled_samples.values()):
                    print("✅ Reached target sample count!")
                    break
            
            # Timeout check
            if (datetime.now() - start_time).total_seconds() > duration_minutes * 60:
                print("⏰ Time limit reached")
                break
                
    except KeyboardInterrupt:
        print("\n⏸️  Collection stopped by user")
    finally:
        consumer.close()
    
    # Final processing
    new_samples = process_events(events_by_zone, labeler)
    for label, samples in new_samples.items():
        labeled_samples[label].extend(samples)
    
    return labeled_samples


def process_events(events_by_zone, labeler):
    """
    Group events into windows and label them.
    Returns dict of {label: [feature_vectors]}
    """
    
    labeled_samples = defaultdict(list)
    
    for zone, events in events_by_zone.items():
        if len(events) < 2:
            continue
        
        # Normalize events - ensure they have 'source' field
        for event in events:
            if 'source' not in event and 'source_type' in event:
                event['source'] = event['source_type']
            if 'score' not in event and 'anomaly_score' in event:
                event['score'] = event['anomaly_score']
        
        # Sort by timestamp
        try:
            events.sort(key=lambda x: datetime.fromisoformat(x['timestamp'].replace('Z', '+00:00')))
        except:
            continue
        
        # Create time windows
        window_start = None
        current_window = []
        
        for event in events:
            try:
                event_time = datetime.fromisoformat(event['timestamp'].replace('Z', '+00:00'))
            except:
                continue
            
            if window_start is None:
                window_start = event_time
                current_window = [event]
            elif event_time - window_start <= timedelta(minutes=WINDOW_SIZE):
                current_window.append(event)
            else:
                # Process window
                if len(current_window) >= 2:
                    window = {
                        'zone': zone,
                        'window_start': window_start,
                        'window_end': event_time,
                        'events': current_window
                    }
                    
                    # Auto-label using rules
                    label = labeler.label_incident(window)
                    
                    if label:
                        # Build features
                        incident = {
                            "sources_involved": list(set(
                                e.get('source', 'unknown')
                                for e in current_window
                            )),
                            "correlated_events": current_window,
                            "time_of_day": window_start.hour
                        }
                        
                        features = IntentFeatureBuilder.build_features(incident)
                        labeled_samples[label].append(features)
                
                # Start new window
                window_start = event_time
                current_window = [event]
        
        # Process last window
        if len(current_window) >= 2:
            window = {
                'zone': zone,
                'window_start': window_start,
                'window_end': datetime.utcnow(),
                'events': current_window
            }
            
            label = labeler.label_incident(window)
            
            if label:
                incident = {
                    "sources_involved": list(set(
                        e.get('source', 'unknown')
                        for e in current_window
                    )),
                    "correlated_events": current_window,
                    "time_of_day": window_start.hour
                }
                
                features = IntentFeatureBuilder.build_features(incident)
                labeled_samples[label].append(features)
    
    # Clear processed events
    events_by_zone.clear()
    
    return labeled_samples


# ============================================================
# Save Dataset
# ============================================================

def save_dataset(labeled_samples):
    """Save to CSV"""
    
    if not labeled_samples:
        print("\n⚠️  No labeled data collected!")
        print("Make sure:")
        print("1. Kafka is running")
        print("2. Anomaly events are being published")
        print("3. Events match correlation rules")
        return False
    
    rows = []
    labels = []
    
    for label, feature_list in labeled_samples.items():
        for features in feature_list:
            rows.append(features)
            labels.append(label)
    
    df = pd.DataFrame(rows, columns=FEATURE_ORDER)
    df['label'] = labels
    
    # Balance classes (downsample to smallest class)
    min_count = df['label'].value_counts().min()
    df_balanced = df.groupby('label', group_keys=False).apply(
        lambda x: x.sample(min(len(x), min_count * 2))  # Allow 2x smallest
    )
    
    import os
    os.makedirs('data/processed', exist_ok=True)
    df_balanced.to_csv(OUTPUT_PATH, index=False)
    
    print(f"\n✅ Dataset saved to {OUTPUT_PATH}")
    print(f"Total samples: {len(df_balanced)}")
    print("\nClass distribution:")
    print(df_balanced['label'].value_counts())
    
    return True


# ============================================================
# Main
# ============================================================

def main():
    print("\n" + "="*80)
    print("  AUTOMATED INTENT TRAINING DATA BUILDER")
    print("="*80)
    print("\nThis tool automatically labels incidents using correlation rules.")
    print("No manual labeling required!\n")
    
    # Collect and auto-label
    labeled_samples = collect_and_label(
        duration_minutes=10,
        min_samples_per_class=50
    )
    
    # Save dataset
    success = save_dataset(labeled_samples)
    
    if success:
        print("\n🎯 Next steps:")
        print("1. cd intent_model")
        print("2. python train_intent_classifier.py")
        print("3. python evaluate.py")
    else:
        print("\n⚠️  Not enough data collected.")
        print("Options:")
        print("1. Let Kafka collect more events, then run again")
        print("2. Use synthetic data: python generate_synthetic_incidents.py")


if __name__ == "__main__":
    main()