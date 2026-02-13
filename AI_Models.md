# ThreatLens AI — Complete I/O & Model Specification

---

## AI Engineer Responsibilities Split

| | P3 — AI/ML Engineer 1 | P4 — AI/ML Engineer 2 |
|---|---|---|
| **Focus** | Detection, Correlation, Scoring | Vision, Sandbox, Explanation |
| **Models** | Isolation Forest, Autoencoder, Random Forest, LSTM, Intent Classifier, Predictive Engine | YOLOv8, DeepSORT, Sandbox Behavior Classifier, NLG Engine, LLM Copilot |
| **Data** | Network flows, logs, RF signals, file events | Camera frames, sandbox execution traces |
| **XAI** | SHAP values for all ML models | NLG template filling, LLM context injection |

---

## STAGE 1: Data Ingestion
**Owner: P2**

---

### 1A — Network Traffic

**Input:**
```
UNSW-NB15 dataset CSV row:
srcip, sport, dstip, dsport, proto, 
dur, sbytes, dbytes, sttl, dttl,
sloss, dloss, service, sload, dload,
spkts, dpkts, swin, dwin, stcpb,
dtcpb, smeansz, dmeansz, trans_depth,
res_bdy_len, sjit, djit, stime, ltime,
sintpkt, dintpkt, tcprtt, synack, 
ackdat, is_sm_ips_ports, ct_state_ttl,
ct_flw_http_mthd, is_ftp_login,
ct_ftp_cmd, ct_srv_src, ct_srv_dst,
ct_dst_ltm, ct_src_ltm, ct_src_dport_ltm,
ct_dst_sport_ltm, ct_dst_src_ltm, label
```

**Output (Kafka: `raw-network`):**
```json
{
  "event_id": "net-550e8400",
  "source_type": "network",
  "timestamp": "2024-01-15T02:04:23.000Z",
  "src_ip": "192.168.1.157",
  "dst_ip": "203.0.113.5",
  "src_port": 54231,
  "dst_port": 443,
  "protocol": "tcp",
  "bytes_sent": 2400000000,
  "bytes_received": 1200,
  "duration_seconds": 34.2,
  "packets_sent": 1842,
  "packets_received": 12,
  "service": "https",
  "zone": "internal"
}
```

---

### 1B — Camera Feed

**Input:**
```
cv2.VideoCapture source:
- RTSP stream: rtsp://camera_ip:554/stream
- OR pre-recorded: /data/server_room_footage.mp4
- OR webcam: device index 0

Frame properties:
- Resolution: 1280x720 (HD)
- FPS extracted: 3 frames/second
- Format: BGR numpy array (720, 1280, 3)
```

**Output (Kafka: `raw-camera`):**
```json
{
  "event_id": "cam-550e8401",
  "source_type": "camera",
  "timestamp": "2024-01-15T02:03:12.000Z",
  "camera_id": "CAM_SERVER_ROOM_01",
  "zone": "server_room",
  "frame_path": "/mnt/frames/cam01/frame_020312.jpg",
  "frame_number": 4821,
  "resolution": "1280x720",
  "fps_captured": 3
}
```

---

### 1C — RF Signals

**Input:**
```
Kismet JSON output (real hardware):
{
  "kismet.device.base.macaddr": "AA:BB:CC:DD:EE:FF",
  "kismet.device.base.type": "Wi-Fi AP",
  "kismet.device.base.signal": {
    "kismet.common.signal.last_signal": -45
  },
  "kismet.device.base.frequency": 2437
}

OR simulated fallback CSV:
timestamp, mac, signal_type, frequency_mhz, 
signal_strength_dbm, ssid, zone
```

**Output (Kafka: `raw-rf`):**
```json
{
  "event_id": "rf-550e8402",
  "source_type": "rf",
  "timestamp": "2024-01-15T02:03:05.000Z",
  "mac_address": "AA:BB:CC:DD:EE:FF",
  "signal_type": "wifi",
  "ssid": "UNKNOWN_NET",
  "frequency_mhz": 2437,
  "signal_strength_dbm": -45,
  "zone": "server_room"
}
```

---

### 1D — Device Logs

**Input:**
```
Raw syslog line:
"Jan 15 02:04:05 server-prod-01 sshd[12847]: 
Accepted publickey for admin from 192.168.1.157 
port 54231 ssh2"

OR synthetic log generator output:
flog -t log -f json -n 1000
```

**Output (Kafka: `raw-logs`):**
```json
{
  "event_id": "log-550e8403",
  "source_type": "logs",
  "timestamp": "2024-01-15T02:04:05.000Z",
  "host": "server-prod-01",
  "log_type": "auth",
  "event_type": "ssh_login_success",
  "user": "admin",
  "src_ip": "192.168.1.157",
  "process": "sshd",
  "pid": 12847,
  "zone": "server_room",
  "raw_message": "Accepted publickey for admin from 192.168.1.157"
}
```

---

### 1E — File Integrity

**Input:**
```
Python Watchdog FileSystemEventHandler:
event.event_type: "modified"
event.src_path: "/var/db/customer_data.sql"
event.is_directory: False

File metadata collected on event:
- File size before/after
- SHA-256 hash before/after
- File extension before/after
- Owning process (via psutil)
```

**Output (Kafka: `raw-files`):**
```json
{
  "event_id": "file-550e8404",
  "source_type": "file",
  "timestamp": "2024-01-15T02:05:42.000Z",
  "host": "server-prod-01",
  "file_path": "/var/db/customer_data.sql",
  "event_type": "modified",
  "old_hash": "sha256:abc123def456",
  "new_hash": "sha256:xyz789uvw012",
  "old_extension": ".sql",
  "new_extension": ".encrypted",
  "file_size_bytes": 2400000,
  "process_responsible": "unknown_binary.exe",
  "process_pid": 9823,
  "zone": "server_room"
}
```

---

## STAGE 2: Behavioral DNA Engine
**Owner: P3**

### Model: Exponential Moving Average + Z-Score Statistics
**Not a trained ML model — statistical profiling engine**

**Why this model:**
- No training data required — learns from live data
- Updates continuously — adapts to legitimate behavior changes
- Computationally lightweight — runs on every event in real time
- Interpretable — deviation expressed as standard deviations (sigma)

**Input (all 5 raw Kafka topics simultaneously):**
```python
# Feature extraction per source type

NETWORK_FEATURES = [
    "bytes_sent", "bytes_received", "duration_seconds",
    "packets_sent", "dst_port", "hour_of_day"
]

LOG_FEATURES = [
    "event_type", "hour_of_day", "failed_logins_last_5min",
    "commands_per_hour", "unique_ips_per_hour"
]

CAMERA_FEATURES = [
    "persons_per_hour_in_zone", "occupancy_duration_minutes",
    "hour_of_day"
]

RF_FEATURES = [
    "known_device_count_per_zone", "signal_strength",
    "new_device_appearances_per_hour"
]

FILE_FEATURES = [
    "modifications_per_minute", "unique_processes_writing",
    "extension_change_rate"
]
```

**DNA Profile Store (Redis):**
```json
{
  "entity_id": "192.168.1.157",
  "entity_type": "device",
  "profile": {
    "bytes_sent_per_hour": {
      "mean": 45000000,
      "std": 5000000,
      "sample_count": 2400,
      "ema_alpha": 0.1
    },
    "normal_login_hours": [8, 9, 10, 17, 18],
    "known_destinations": ["10.0.0.1", "10.0.0.5"],
    "last_updated": "2024-01-15T01:00:00Z"
  }
}
```

**Output (Kafka: `dna-enriched-events`):**
```json
{
  "...all original event fields...",
  "dna": {
    "entity_id": "192.168.1.157",
    "deviation_sigma": 8.7,
    "anomalous_metrics": [
      {
        "metric": "bytes_sent",
        "current": 2400000000,
        "baseline_mean": 45000000,
        "baseline_std": 5000000,
        "sigma": 471.0
      },
      {
        "metric": "hour_of_day",
        "current": 2,
        "normal_hours": [8,9,10,17,18],
        "is_normal_hour": false,
        "sigma": 3.2
      }
    ],
    "overall_dna_deviation_score": 87.3
  }
}
```

---

## STAGE 3A: Network Anomaly Detection
**Owner: P3**

### Models: Isolation Forest + Autoencoder (Ensemble)

---

**Model 1: Isolation Forest**

**Why this model:**
- Unsupervised — no labeled attack data needed for training
- Designed specifically for anomaly detection
- Fast inference — real-time capable
- Works well on tabular network flow data
- Industry standard for network anomaly detection

**Training Data:**
```
Dataset: UNSW-NB15 (normal traffic rows only for training)
Normal samples: ~56,000 rows (label=0)
Features used: 20 numerical features
Train/validation split: 80/20
Training time: ~3 minutes on CPU
Library: scikit-learn IsolationForest
Hyperparameters: contamination=0.05, n_estimators=100, random_state=42
```

**Model 2: Autoencoder**

**Why this model:**
- Learns compressed representation of normal traffic
- High reconstruction error = anomalous traffic
- Catches subtle patterns Isolation Forest misses
- Complements Isolation Forest — different error modes

**Architecture:**
```python
Input Layer:     20 features
Encoder:         Dense(64, relu) → Dense(32, relu) → Dense(16, relu)
Bottleneck:      Dense(8, relu)
Decoder:         Dense(16, relu) → Dense(32, relu) → Dense(64, relu)
Output Layer:    Dense(20, linear)
Loss:            Mean Squared Error (reconstruction error)
Optimizer:       Adam, lr=0.001
Epochs:          50
Batch size:      256
Library:         PyTorch
```

**Input to Models:**
```python
# Feature vector (20 features, normalized 0-1)
feature_vector = [
    bytes_sent_normalized,        # MinMaxScaler
    bytes_received_normalized,
    duration_normalized,
    packet_rate_normalized,
    dst_port_normalized,
    protocol_encoded,             # OneHotEncoder
    hour_of_day_normalized,
    dst_ip_reputation_score,      # from threat intel lookup
    src_ip_internal_flag,         # 0 or 1
    connection_state_encoded,
    packets_sent_normalized,
    packets_received_normalized,
    bytes_ratio,                  # sent/received ratio
    packet_size_mean,
    dna_deviation_score_normalized,
    is_known_destination,         # 0 or 1
    service_encoded,
    ttl_normalized,
    jitter_normalized,
    inter_packet_time_normalized
]
```

**Ensemble Scoring:**
```python
if_score = isolation_forest.decision_function([features])
if_normalized = normalize_to_0_100(if_score)

ae_error = mean_squared_error(original, autoencoder(features))
ae_normalized = normalize_to_0_100(ae_error)

final_score = (0.40 * if_normalized) + (0.60 * ae_normalized)
# Autoencoder weighted higher — catches subtle patterns better
```

**Output (Kafka: `network-anomaly-scores`):**
```json
{
  "event_id": "net-550e8400",
  "source_type": "network",
  "timestamp": "2024-01-15T02:04:23.000Z",
  "anomaly_score": 87,
  "model_scores": {
    "isolation_forest": 82,
    "autoencoder_reconstruction_error": 0.91,
    "autoencoder_normalized": 91
  },
  "shap_values": {
    "bytes_sent": 0.45,
    "dst_ip_reputation": 0.30,
    "hour_of_day": 0.15,
    "dst_port": 0.06,
    "duration": 0.04
  },
  "top_features": [
    {"feature": "bytes_sent", "value": 2400000000, "baseline": 45000000, "contribution": 0.45},
    {"feature": "dst_ip_reputation", "value": 0.1, "baseline": 0.9, "contribution": 0.30},
    {"feature": "hour_of_day", "value": 2, "baseline": 10, "contribution": 0.15}
  ],
  "all_original_fields": "..."
}
```

---

## STAGE 3B: Log Anomaly Detection
**Owner: P3**

### Models: Random Forest + LSTM (Ensemble)

---

**Model 1: Random Forest**

**Why this model:**
- Handles mixed categorical + numerical log features well
- Gives natural feature importance scores (compatible with SHAP)
- Fast training — can retrain periodically as new patterns emerge
- Good at detecting known attack patterns in logs

**Training Data:**
```
Dataset: Synthetic logs generated by flog + manually crafted attack sequences
Normal events: login_success, file_access, process_start (labeled 0)
Attack events: brute_force, priv_escalation, lateral_move (labeled 1)
Samples: 10,000 normal + 2,000 attack
Library: scikit-learn RandomForestClassifier
Hyperparameters: n_estimators=200, max_depth=15, random_state=42
Training time: ~2 minutes
```

**Model 2: LSTM Sequence Detector**

**Why this model:**
- Logs tell a story — LSTM reads the story, not just individual lines
- Detects multi-step attack progressions (failed login → success → escalation)
- Catches low-and-slow attacks that single-event models miss
- Random Forest catches single events; LSTM catches sequences

**Architecture:**
```python
Input:           Sequence of last 10 log events per host
Each event:      Encoded as vector of 15 features
Input shape:     (batch_size, 10, 15)
LSTM Layer 1:    LSTM(64, return_sequences=True)
Dropout:         0.2
LSTM Layer 2:    LSTM(32)
Dropout:         0.2
Dense:           Dense(16, relu)
Output:          Dense(1, sigmoid) — anomaly probability
Loss:            Binary Crossentropy
Optimizer:       Adam, lr=0.001
Epochs:          30
Library:         PyTorch
```

**Input to Models:**
```python
# Per-event feature vector (15 features)
log_features = [
    event_type_encoded,           # LabelEncoder: 0-20
    hour_of_day,                  # 0-23
    day_of_week,                  # 0-6
    failed_logins_last_5min,      # integer count
    is_new_source_ip,             # 0 or 1
    privilege_level,              # 0=user, 1=sudo, 2=root
    command_risk_score,           # 0-1 based on command whitelist
    is_first_time_user_host,      # 0 or 1
    time_since_last_event_sec,    # seconds
    process_whitelisted,          # 0 or 1
    destination_ip_internal,      # 0 or 1
    auth_method_encoded,          # password=0, key=1, cert=2
    dna_deviation_score,          # from Stage 2
    consecutive_failures,         # count of recent failures
    session_duration_seconds      # how long session has been open
]

# LSTM input: last 10 events as ordered sequence
sequence_input = [log_features_t-9, ..., log_features_t-1, log_features_t]
# shape: (1, 10, 15)
```

**Ensemble Scoring:**
```python
rf_prob = random_forest.predict_proba([features])[0][1]
rf_score = rf_prob * 100

lstm_prob = lstm_model(sequence_tensor).item()
lstm_score = lstm_prob * 100

final_score = (0.45 * rf_score) + (0.55 * lstm_score)
# LSTM weighted slightly higher — sequence context more valuable
```

**Output (Kafka: `log-anomaly-scores`):**
```json
{
  "event_id": "log-550e8403",
  "source_type": "logs",
  "timestamp": "2024-01-15T02:04:05.000Z",
  "anomaly_score": 76,
  "model_scores": {
    "random_forest_probability": 0.71,
    "random_forest_score": 71,
    "lstm_sequence_probability": 0.81,
    "lstm_score": 81
  },
  "sequence_pattern": "auth_failure × 5 → auth_success → privilege_escalation",
  "shap_values": {
    "is_new_source_ip": 0.40,
    "hour_of_day": 0.35,
    "consecutive_failures": 0.25
  },
  "top_features": [
    {"feature": "is_new_source_ip", "value": true, "contribution": 0.40},
    {"feature": "hour_of_day", "value": 2, "baseline": 9, "contribution": 0.35},
    {"feature": "consecutive_failures", "value": 7, "baseline": 0.2, "contribution": 0.25}
  ],
  "all_original_fields": "..."
}
```

---

## STAGE 3C: Camera Anomaly Detection
**Owner: P4**

### Models: YOLOv8 + DeepSORT + Rule Engine

---

**Model 1: YOLOv8n (nano)**

**Why this model:**
- State of the art real-time object detection
- nano variant balances speed vs accuracy for real-time processing
- Pre-trained on COCO — detects persons out of the box, no training needed
- Runs at 30+ FPS on CPU — fast enough for 3 FPS camera ingestion

**Model 2: DeepSORT**

**Why this model:**
- Assigns persistent IDs to tracked persons across frames
- Combines appearance features + motion prediction
- Critical differentiator — know it's the SAME person across cameras
- Catches tailgating (2 persons enter but only 1 badge scan)

**No training needed — both models used pretrained**

**Input:**
```python
# Raw frame from Kafka
frame = cv2.imread(frame_path)
# Shape: (720, 1280, 3) BGR numpy array

# Zone definitions (configured per deployment)
ZONES = {
    "server_room": {
        "polygon": [(100,200), (800,200), (800,600), (100,600)],
        "permitted_hours": (8, 18),  # 8AM to 6PM
        "max_persons": 2,
        "requires_badge": True
    },
    "lobby": {
        "polygon": [(0,0), (1280,0), (1280,400), (0,400)],
        "permitted_hours": (6, 22),
        "max_persons": 50,
        "requires_badge": False
    }
}
```

**Processing Pipeline:**
```python
# Step 1: YOLOv8 detection
results = yolo_model(frame, classes=[0])  # class 0 = person only
detections = []
for box in results[0].boxes:
    x1,y1,x2,y2 = box.xyxy[0]
    confidence = box.conf[0]
    detections.append([x1,y1,x2,y2,confidence])

# Step 2: DeepSORT tracking
tracked = deepsort.update(detections, frame)
# Returns: [[x1,y1,x2,y2, track_id], ...]

# Step 3: Zone rule checking
for person in tracked:
    person_center = get_center(person[:4])
    zone = get_zone(person_center, ZONES)
    track_id = person[4]
    
    violations = []
    if zone["requires_badge"]:
        if not badge_scan_recorded(track_id, timestamp):
            violations.append("no_badge_scan")
    if not in_permitted_hours(timestamp, zone["permitted_hours"]):
        violations.append("after_hours")
    if loitering_detected(track_id, zone, threshold_minutes=5):
        violations.append("loitering")

# Step 4: Annotate frame
annotated = draw_boxes_and_zones(frame, tracked, violations)
cv2.imwrite(annotated_frame_path, annotated)
```

**Rule Engine — Anomaly Scoring:**
```python
base_score = 0
if "no_badge_scan" in violations:    base_score += 40
if "after_hours" in violations:      base_score += 30
if "loitering" in violations:        base_score += 20
if "restricted_zone" in violations:  base_score += 30
if confidence > 0.90:                base_score *= 1.1

anomaly_score = min(100, base_score)
```

**Output (Kafka: `camera-anomaly-scores`):**
```json
{
  "event_id": "cam-550e8401",
  "source_type": "camera",
  "timestamp": "2024-01-15T02:03:12.000Z",
  "anomaly_score": 92,
  "persons_detected": 1,
  "tracked_persons": [
    {
      "track_id": "PERSON_7743",
      "bounding_box": [120, 80, 340, 460],
      "confidence": 0.94,
      "zone": "server_room",
      "violations": ["no_badge_scan", "after_hours"],
      "time_in_zone_minutes": 0.2
    }
  ],
  "zone_violations": true,
  "violation_types": ["no_badge_scan", "after_hours"],
  "permitted_hours": "08:00-18:00",
  "current_time": "02:03",
  "annotated_frame_path": "/mnt/evidence/cam01/annotated_020312.jpg",
  "raw_frame_path": "/mnt/frames/cam01/frame_020312.jpg"
}
```

---

## STAGE 3D: RF Anomaly Detection
**Owner: P3**

### Model: Whitelist Comparator + Statistical Z-Score
**Not an ML model — deterministic + statistical**

**Why this approach:**
- RF anomaly is binary in nature — device is known or unknown
- No training data needed
- Zero false negatives on unknown device detection
- Statistical layer catches jamming patterns

**Input:**
```python
# Raw RF event from Kafka
rf_event = {
    "mac_address": "AA:BB:CC:DD:EE:FF",
    "signal_type": "wifi",
    "frequency_mhz": 2437,
    "signal_strength_dbm": -45,
    "zone": "server_room"
}

# Known device whitelist (JSON config file)
WHITELIST = {
    "AA:BB:CC:11:22:33": {"name": "AP_ServerRoom", "type": "access_point"},
    "DD:EE:FF:44:55:66": {"name": "Laptop_Admin", "type": "laptop"}
}

# Historical signal baselines per zone (Redis)
SIGNAL_BASELINE = {
    "server_room": {
        "mean_device_count": 4,
        "std_device_count": 0.5,
        "mean_signal_dbm": -55,
        "std_signal_dbm": 8
    }
}
```

**Processing:**
```python
# Check 1: Whitelist
is_known = rf_event["mac_address"] in WHITELIST
whitelist_score = 0 if is_known else 70

# Check 2: Signal strength anomaly
signal_z = abs(rf_event["signal_strength_dbm"] - 
               SIGNAL_BASELINE[zone]["mean_signal_dbm"]) / \
               SIGNAL_BASELINE[zone]["std_signal_dbm"]
signal_score = min(30, signal_z * 10)

# Check 3: Jamming detection
# Jamming = multiple frequencies simultaneously disrupted
jamming_detected = check_frequency_sweep(recent_rf_events)
jamming_score = 90 if jamming_detected else 0

final_score = max(whitelist_score + signal_score, jamming_score)
```

**Output (Kafka: `rf-anomaly-scores`):**
```json
{
  "event_id": "rf-550e8402",
  "source_type": "rf",
  "timestamp": "2024-01-15T02:03:05.000Z",
  "anomaly_score": 85,
  "is_whitelisted": false,
  "mac_address": "AA:BB:CC:DD:EE:FF",
  "signal_type": "wifi",
  "anomaly_breakdown": {
    "unknown_device_score": 70,
    "signal_anomaly_score": 15,
    "jamming_detected": false,
    "jamming_score": 0
  },
  "zone": "server_room",
  "new_device_in_restricted_zone": true
}
```

---

## STAGE 3E: File Integrity Anomaly Detection
**Owner: P3**

### Model: Rule Engine + Isolation Forest (secondary)

**Why this approach:**
- File events are highly interpretable — rule-based catches obvious cases
- Isolation Forest catches subtle deviations in file modification patterns
- Two-layer approach minimizes false negatives

**Input:**
```python
# File event from Kafka
file_event = {
    "file_path": "/var/db/customer_data.sql",
    "event_type": "modified",
    "old_extension": ".sql",
    "new_extension": ".encrypted",
    "process_responsible": "unknown_binary.exe",
    "process_pid": 9823,
    "file_size_bytes": 2400000
}

# Context from Redis (recent file events)
recent_modifications = {
    "modifications_last_60s": 847,
    "unique_extensions_changed": 12,
    "processes_writing": ["unknown_binary.exe"]
}

# Process whitelist
PROCESS_WHITELIST = ["vim", "nano", "python3", "rsync", "cp", "mv"]
```

**Rule Layer:**
```python
score = 0
reasons = []

# Rule 1: Extension change (ransomware indicator)
if old_ext != new_ext:
    score += 35
    reasons.append("extension_changed")

# Rule 2: Unknown process writing
if process not in PROCESS_WHITELIST:
    score += 30
    reasons.append("unknown_process")

# Rule 3: Mass modification (ransomware pattern)
if modifications_last_60s > 100:
    score += 25
    reasons.append("mass_modification")
    if modifications_last_60s > 500:
        score += 10  # bonus for severe ransomware rate

# Rule 4: Sensitive directory
SENSITIVE_DIRS = ["/var/db", "/etc", "/home", "/root"]
if any(file_path.startswith(d) for d in SENSITIVE_DIRS):
    score += 10
    reasons.append("sensitive_directory")

rule_score = min(100, score)
```

**Isolation Forest (secondary layer):**
```python
# Features for IF model
file_features = [
    modifications_per_minute,
    unique_processes_writing,
    extension_change_rate,
    file_size_change_ratio,
    sensitive_dir_access_rate,
    hour_of_day
]
# Trained on normal file activity patterns
if_score = isolation_forest_file.predict([file_features])
```

**Output (Kafka: `file-anomaly-scores`):**
```json
{
  "event_id": "file-550e8404",
  "source_type": "file",
  "timestamp": "2024-01-15T02:05:42.000Z",
  "anomaly_score": 91,
  "model_scores": {
    "rule_engine_score": 95,
    "isolation_forest_score": 87,
    "ensemble": 91
  },
  "triggered_rules": [
    "extension_changed",
    "unknown_process",
    "mass_modification",
    "sensitive_directory"
  ],
  "ransomware_pattern": true,
  "files_modified_last_60s": 847,
  "process_whitelisted": false,
  "sandbox_trigger": true,
  "shap_values": {
    "extension_change": 0.40,
    "unknown_process": 0.35,
    "mass_modification_rate": 0.25
  },
  "all_original_fields": "..."
}
```

---

## STAGE 4: Cross-Domain Correlation Engine
**Owner: P3**

### Model: Rule Engine + Random Forest Intent Classifier + Markov Chain Predictor

---

**Input (all 5 anomaly score Kafka topics, threshold filter > 40):**
```python
# Events entering correlation window
event_window = {
    "window_id": "WIN-2024-001",
    "window_start": "2024-01-15T02:00:00Z",
    "window_end": "2024-01-15T02:15:00Z",
    "events": [
        {"event_id": "cam-550e8401", "source": "camera", "score": 92, "zone": "server_room", "timestamp": "02:03:12"},
        {"event_id": "log-550e8403", "source": "logs", "score": 76, "zone": "server_room", "timestamp": "02:04:05"},
        {"event_id": "file-550e8404", "source": "file", "score": 91, "zone": "server_room", "timestamp": "02:05:42"},
        {"event_id": "net-550e8400", "source": "network", "score": 87, "zone": "internal", "timestamp": "02:06:19"}
    ]
}
```

**Correlation Rule Matching:**
```python
CORRELATION_RULES = [
    {
        "rule_id": "RULE_001",
        "name": "Insider Data Theft",
        "required_sources": ["camera", "logs", "network"],
        "optional_sources": ["file"],
        "time_window_minutes": 10,
        "min_scores": {"camera": 70, "logs": 60, "network": 70},
        "zone_match_required": True,
        "risk_multiplier": 1.8,
        "mitre_ttps": ["T1078", "T1041"],
        "intent_label": "data_exfiltration"
    },
    {
        "rule_id": "RULE_002",
        "name": "Ransomware Deployment",
        "required_sources": ["file"],
        "optional_sources": ["network", "logs"],
        "time_window_minutes": 5,
        "min_scores": {"file": 80},
        "ransomware_pattern_required": True,
        "risk_multiplier": 2.0,
        "mitre_ttps": ["T1486", "T1490"],
        "intent_label": "ransomware"
    },
    {
        "rule_id": "RULE_003",
        "name": "Physical + Cyber Coordinated",
        "required_sources": ["camera", "logs"],
        "optional_sources": ["network", "rf"],
        "time_window_minutes": 5,
        "risk_multiplier": 1.6,
        "mitre_ttps": ["T1078", "T1098"],
        "intent_label": "apt_infiltration"
    }
    # 12+ more rules...
]
```

**Risk Scoring Formula:**
```python
def calculate_risk_score(events, matched_rule):
    weights = {
        "network": 0.30, "logs": 0.25,
        "camera": 0.25, "file": 0.15, "rf": 0.05
    }
    
    base_score = sum(
        events[src]["score"] * weights[src]
        for src in events
    )
    
    sources_count = len(events)
    correlation_multiplier = {1: 1.0, 2: 1.3, 3: 1.6, 4: 2.0}[min(sources_count, 4)]
    
    mitre_severity = {"low": 1.0, "medium": 1.3, "high": 1.6, "critical": 2.0}
    mitre_weight = mitre_severity[get_mitre_severity(matched_rule["mitre_ttps"])]
    
    final = base_score * correlation_multiplier * matched_rule["risk_multiplier"]
    return min(100, final)
```

**Intent Classifier Model:**

**Why Random Forest:**
- Multi-class classification with structured input
- Fast inference — runs per incident
- SHAP compatible for explaining why intent was classified

```python
# Training data: MITRE ATT&CK TTP sequences per attack type
# Features: which sources triggered, which rules matched, TTP codes
# Labels: ransomware, data_exfiltration, apt, insider_threat, 
#         reconnaissance, sabotage, ddos

intent_features = [
    camera_triggered,        # 0 or 1
    network_triggered,       # 0 or 1
    logs_triggered,          # 0 or 1
    file_triggered,          # 0 or 1
    rf_triggered,            # 0 or 1
    has_mass_encryption,     # 0 or 1
    has_large_transfer,      # 0 or 1
    has_physical_intrusion,  # 0 or 1
    has_c2_beaconing,        # 0 or 1
    has_privilege_escalation,# 0 or 1
    time_of_day,
    correlation_window_minutes,
    max_anomaly_score,
    sources_count
]

intent_classifier = RandomForestClassifier(n_estimators=100)
# Trained on synthetic incident data labeled by attack type
```

**Predictive Next-Move Engine:**

**Why Markov Chain:**
- Attack stages follow probabilistic sequences
- Simple to implement, interpretable output
- Based on established MITRE ATT&CK kill chain progressions

```python
# Transition matrix from MITRE ATT&CK historical data
ATTACK_TRANSITIONS = {
    "reconnaissance": {
        "initial_access": 0.70,
        "reconnaissance": 0.20,
        "none": 0.10
    },
    "initial_access": {
        "execution": 0.40,
        "persistence": 0.30,
        "lateral_movement": 0.20,
        "none": 0.10
    },
    "execution": {
        "persistence": 0.35,
        "exfiltration": 0.35,
        "impact": 0.20,
        "none": 0.10
    }
}

def predict_next_move(current_stage):
    transitions = ATTACK_TRANSITIONS[current_stage]
    next_stage = max(transitions, key=transitions.get)
    confidence = transitions[next_stage]
    return next_stage, confidence
```

**Output (Kafka: `correlated-incidents`):**
```json
{
  "incident_id": "INC-2024-001",
  "timestamp": "2024-01-15T02:07:01.000Z",
  "risk_score": 94,
  "severity": "CRITICAL",
  "matched_rule": "RULE_001",
  "rule_name": "Insider Data Theft",
  "correlated_events": [
    {"event_id": "cam-550e8401", "source": "camera", "score": 92, "timestamp": "02:03:12"},
    {"event_id": "log-550e8403", "source": "logs", "score": 76, "timestamp": "02:04:05"},
    {"event_id": "file-550e8404", "source": "file", "score": 91, "timestamp": "02:05:42"},
    {"event_id": "net-550e8400", "source": "network", "score": 87, "timestamp": "02:06:19"}
  ],
  "sources_involved": ["camera", "logs", "file", "network"],
  "correlation_window_minutes": 4,
  "risk_breakdown": {
    "base_weighted_score": 86.5,
    "correlation_multiplier": 2.0,
    "rule_multiplier": 1.8,
    "final_capped": 94
  },
  "intent": {
    "primary": "data_exfiltration",
    "primary_confidence": 0.94,
    "secondary": "insider_threat",
    "secondary_confidence": 0.81
  },
  "mitre_ttps": ["T1078", "T1041", "T1486"],
  "current_attack_stage": "exfiltration",
  "predicted_next_move": {
    "stage": "log_deletion",
    "mitre_ttp": "T1070",
    "confidence": 0.78,
    "expected_within_minutes": 15,
    "warning": "Attacker likely to delete logs to cover tracks"
  },
  "evidence_capture_trigger": true,
  "sandbox_trigger": true,
  "neo4j_node_ids": ["node-001", "node-002", "node-003", "node-004"]
}
```

---

## STAGE 5: Evidence Capture
**Owner: P4**

**Input:**
```json
{
  "incident_id": "INC-2024-001",
  "correlated_events": [...],
  "timestamp_range": {
    "start": "2024-01-15T02:03:00Z",
    "end": "2024-01-15T02:07:30Z"
  },
  "sources_involved": ["camera", "logs", "file", "network"],
  "zone": "server_room"
}
```

**Processing per source:**
```python
# Camera: extract video clip
ffmpeg -i /recordings/cam01.mp4 
       -ss 02:03:07 -to 02:03:17 
       /evidence/INC-2024-001/camera/clip.mp4

# Logs: Elasticsearch query
GET /logs/_search {
  "query": {
    "bool": {
      "filter": [
        {"range": {"timestamp": {"gte": "02:03:00", "lte": "02:07:30"}}},
        {"term": {"zone": "server_room"}}
      ]
    }
  }
}

# Network: tcpdump packet capture
tcpdump -i eth0 
        "host 203.0.113.5" 
        -w /evidence/INC-2024-001/network/capture.pcap
        -c 1000

# File: copy suspicious file
cp /var/db/customer_data.sql.encrypted 
   /evidence/INC-2024-001/files/
sha256sum /evidence/INC-2024-001/files/* > hashes.txt
```

**Output (Kafka: `evidence-manifest`):**
```json
{
  "incident_id": "INC-2024-001",
  "capture_timestamp": "2024-01-15T02:07:15.000Z",
  "evidence": {
    "camera": {
      "video_clip": "/evidence/INC-2024-001/camera/clip.mp4",
      "annotated_frames": [
        "/evidence/INC-2024-001/camera/frame_020312_annotated.jpg"
      ],
      "clip_duration_seconds": 10
    },
    "logs": {
      "log_snippet_path": "/evidence/INC-2024-001/logs/auth_snippet.txt",
      "event_count": 23,
      "time_range": "±30 seconds"
    },
    "network": {
      "pcap_path": "/evidence/INC-2024-001/network/capture.pcap",
      "packets_captured": 1000,
      "flow_summary": "2.3GB to 203.0.113.5:443"
    },
    "files": {
      "suspicious_file": "/evidence/INC-2024-001/files/customer_data.sql.encrypted",
      "sha256": "sha256:deadbeef...",
      "original_path": "/var/db/customer_data.sql"
    }
  },
  "total_size_mb": 48.3,
  "ready_for_blockchain": true
}
```

---

## STAGE 6: Sandbox Detonation
**Owner: P4**

### Model: Behavioral Rule Classifier (post-execution analysis)

**Input:**
```json
{
  "incident_id": "INC-2024-001",
  "file_to_detonate": "/evidence/INC-2024-001/files/unknown_binary.exe",
  "file_hash": "sha256:deadbeef...",
  "file_type": "PE32 executable",
  "trigger_reason": "unknown_process + mass_encryption_pattern"
}
```

**Sandbox Container Startup:**
```bash
docker run --rm \
  --network=none \          # complete network isolation
  --memory=512m \           # limit resources
  --cpus=1 \
  --name=sandbox_INC2024001 \
  threatlens-sandbox:latest

# Inside container monitoring agents:
auditd -f &                 # file system monitoring
tcpdump -i any -w /out/net.pcap &  # network monitoring
Xvfb :99 &                  # virtual display
x11vnc -display :99 &       # VNC for screenshots
```

**Screenshot Capture Loop (P4 implements):**
```python
import pyautogui
import time

screenshots = []
for i in range(60):  # 120 seconds / 2 second interval
    screenshot = pyautogui.screenshot()
    path = f"/evidence/INC-2024-001/sandbox/frame_{i:04d}.jpg"
    screenshot.save(path)
    screenshots.append(path)
    time.sleep(2)
```

**Post-Execution Behavioral Analysis:**
```python
# Behavioral Rule Classifier
# NOT an ML model — deterministic rules on observed behavior
def classify_sandbox_verdict(behavior_log):
    score = 0
    indicators = []
    
    if behavior_log["files_encrypted"] > 10:
        score += 40; indicators.append("ransomware_encryption")
    if behavior_log["ransom_note_created"]:
        score += 30; indicators.append("ransom_note")
    if behavior_log["network_connections"]:
        score += 20; indicators.append("c2_callback_attempted")
    if behavior_log["persistence_mechanisms"]:
        score += 15; indicators.append("persistence_established")
    if behavior_log["shadow_copies_deleted"]:
        score += 25; indicators.append("backup_destruction")
    if behavior_log["processes_spawned_suspicious"]:
        score += 10; indicators.append("suspicious_child_process")
    
    if score >= 70:   verdict = "MALICIOUS"
    elif score >= 40: verdict = "SUSPICIOUS"
    else:             verdict = "BENIGN"
    
    return verdict, score, indicators
```

**Output (Kafka: `sandbox-results`):**
```json
{
  "incident_id": "INC-2024-001",
  "file_hash": "sha256:deadbeef...",
  "verdict": "MALICIOUS",
  "confidence_score": 97,
  "detonation_duration_seconds": 120,
  "behavioral_summary": {
    "files_created": ["/tmp/.hidden", "C:/ransom_note.txt"],
    "files_encrypted": 847,
    "registry_modified": ["HKCU\\Run\\persist_malware"],
    "shadow_copies_deleted": true,
    "processes_spawned": ["cmd.exe", "vssadmin.exe", "wevtutil.exe"],
    "network_connections_attempted": [
      {"ip": "203.0.113.5", "port": 443, "domain": "evil-c2.ru"},
      {"ip": "198.51.100.3", "port": 8080}
    ]
  },
  "extracted_iocs": {
    "ips": ["203.0.113.5", "198.51.100.3"],
    "domains": ["evil-c2.ru"],
    "file_hashes": ["sha256:deadbeef...", "sha256:cafebabe..."],
    "registry_keys": ["HKCU\\Run\\persist_malware"],
    "mitre_behaviors": ["T1486", "T1490", "T1071", "T1547"]
  },
  "screenshot_sequence": [
    "/evidence/INC-2024-001/sandbox/frame_0000.jpg",
    "/evidence/INC-2024-001/sandbox/frame_0001.jpg",
    "... 58 more ..."
  ]
}
```

---

## STAGE 7A: SHAP Explanations
**Owner: P3**

**Input:**
```python
# Already computed in Stages 3A-3E
# SHAP explainer initialized once at model load time

import shap
# For Random Forest (logs, file, intent)
rf_explainer = shap.TreeExplainer(random_forest_model)

# For Isolation Forest (network)
if_explainer = shap.TreeExplainer(isolation_forest_model)

# For Autoencoder — use KernelSHAP (slower but works)
ae_explainer = shap.KernelExplainer(autoencoder_predict, background_data)

# Input: feature vector that produced anomaly score
shap_values = rf_explainer.shap_values(feature_vector)
```

**Output (attached to anomaly score events, passed to NLG):**
```json
{
  "event_id": "log-550e8403",
  "shap_explanation": {
    "expected_value": 45.2,
    "model_output": 76.0,
    "features": [
      {"name": "is_new_source_ip", "value": 1, "shap": 12.4, "direction": "increases_risk"},
      {"name": "hour_of_day", "value": 2, "shap": 10.8, "direction": "increases_risk"},
      {"name": "consecutive_failures", "value": 7, "shap": 8.1, "direction": "increases_risk"},
      {"name": "process_whitelisted", "value": 0, "shap": 5.2, "direction": "increases_risk"},
      {"name": "privilege_level", "value": 2, "shap": -2.1, "direction": "decreases_risk"}
    ],
    "plot_type": "waterfall",
    "serialized_for_frontend": "base64_chart_data..."
  }
}
```

---

## STAGE 7B: NLG Explanation Generator
**Owner: P4**

### Model: Template Engine (deterministic, no hallucination)

**Input:**
```json
{
  "incident": "full correlated incident JSON from Stage 4",
  "shap_explanations": "SHAP outputs for all involved events",
  "sandbox_result": "sandbox result JSON from Stage 6 (if available)",
  "dna_deviations": "DNA deviation data from Stage 2"
}
```

**Template System:**
```python
EXPLANATION_TEMPLATES = {
    "camera": "Unauthorized person detected in {zone} at {timestamp}. "
              "Access occurred {hours_outside} hours outside permitted window "
              "({permitted_start}-{permitted_end}). "
              "No badge scan recorded at entry point. "
              "Person tracked as ID #{reid_token}.",

    "logs": "SSH login from {src_ip} at {timestamp}. "
            "This IP {ip_history}. "
            "Login preceded by {failure_count} failed attempts. "
            "Privilege level escalated to {privilege_level} "
            "{time_after_login} seconds after initial login.",

    "network": "Outbound transfer of {transfer_size}GB to {dst_ip} at {timestamp}. "
               "Destination has {dst_history}. "
               "Transfer volume is {volume_multiple}x the baseline. "
               "Traffic pattern matches {traffic_pattern}.",

    "file": "{file_count} files in {directory} {modification_type} within "
            "{time_window} seconds by process {process_name} "
            "({process_status}). {extension_change_statement}.",

    "correlation": "All {source_count} events occurred within a "
                   "{window_minutes}-minute window. "
                   "Temporal sequence ({sequence}) matches "
                   "{attack_pattern} attack pattern.",

    "sandbox": "Sandbox analysis of {filename} confirms {verdict}. "
               "File {sandbox_actions}. "
               "C2 callback attempted to {c2_domains}. "
               "{ioc_count} IOCs extracted and blacklisted.",

    "prediction": "Based on current attack stage ({current_stage}), "
                  "system predicts {next_stage} attempt within "
                  "{time_estimate} minutes (confidence: {confidence}%). "
                  "Recommended action: {recommendation}."
}
```

**Output (Kafka: `nlg-explanations`):**
```json
{
  "incident_id": "INC-2024-001",
  "risk_score": 94,
  "severity": "CRITICAL",
  "intent": "DATA EXFILTRATION",
  "summary": "CRITICAL: Coordinated insider data theft detected. Risk score 94/100.",
  "sections": [
    {
      "source": "Camera",
      "score": 92,
      "icon": "camera",
      "text": "Unauthorized person detected in Server Room at 02:03 AM. Access occurred 8 hours outside permitted window (08:00-18:00). No badge scan recorded at entry point. Person tracked as ID #7743.",
      "key_factors": ["after_hours", "no_badge_scan", "restricted_zone"]
    },
    {
      "source": "System Logs",
      "score": 76,
      "icon": "terminal",
      "text": "SSH login from 192.168.1.157 at 02:04 AM. This IP has never previously authenticated on this subnet. Login preceded by 7 failed attempts. Privilege escalated to root 53 seconds after login.",
      "key_factors": ["new_ip", "after_failures", "privilege_escalation"]
    },
    {
      "source": "File Integrity",
      "score": 91,
      "icon": "file-warning",
      "text": "847 files in /var/db/ modified within 60 seconds by process unknown_binary.exe (not whitelisted). File extensions changed from .sql to .encrypted — ransomware encryption pattern confirmed.",
      "key_factors": ["mass_modification", "unknown_process", "extension_change"]
    },
    {
      "source": "Network",
      "score": 87,
      "icon": "network",
      "text": "Outbound transfer of 2.3GB to 203.0.113.5 at 02:06 AM. Destination has no prior history in network baseline. Volume is 53x hourly baseline. Traffic pattern matches data exfiltration.",
      "key_factors": ["unknown_destination", "volume_anomaly", "off_hours"]
    }
  ],
  "correlation_statement": "All 4 events within 4-minute window. Sequence (physical entry → login → file encryption → exfiltration) matches insider data theft TTP.",
  "mitre_statement": "Matches T1078 (Valid Accounts) + T1041 (Exfiltration Over C2).",
  "sandbox_statement": "Sandbox confirmed MALICIOUS — encryption routine, C2 callback to evil-c2.ru, ransom note dropped.",
  "prediction_statement": "Attacker likely to attempt log deletion (T1070) within 15 minutes. Recommend immediate host isolation.",
  "recommended_actions": [
    "Isolate host server-prod-01 from network",
    "Block outbound IP 203.0.113.5",
    "Revoke admin credentials for session from 192.168.1.157",
    "Dispatch physical security to Server Room",
    "Preserve logs before deletion attempt"
  ]
}
```

---

## STAGE 7C: LLM SOC Copilot
**Owner: P4**

### Model: Mistral-7B via Ollama (local, no external API)

**Why Mistral-7B:**
- Runs locally — no API cost, no data privacy concern
- 7B parameters — fits in 8GB RAM
- Strong instruction following — handles analyst questions well
- Fast enough for interactive use (~2-3 second response)

**Input:**
```python
# Analyst question (from dashboard chat UI)
question = "What happened in the server room last night?"

# Context retrieval (Elasticsearch query based on question)
context_events = elasticsearch.search(
    index="events",
    body={
        "query": {
            "bool": {
                "filter": [
                    {"term": {"zone": "server_room"}},
                    {"range": {"timestamp": {"gte": "now-24h"}}}
                ]
            }
        },
        "size": 20,
        "sort": [{"timestamp": "asc"}]
    }
)

# Build LLM prompt
prompt = f"""
You are a cybersecurity analyst assistant.
Answer the analyst's question using ONLY the provided security event data.
Do not invent or assume any information not in the data.

SECURITY EVENT DATA:
{json.dumps(context_events, indent=2)}

ANALYST QUESTION: {question}

Provide a clear, concise summary suitable for a SOC analyst.
Reference specific timestamps and scores from the data.
"""
```

**LLM Processing:**
```python
import ollama

response = ollama.chat(
    model="mistral:7b",
    messages=[{"role": "user", "content": prompt}],
    options={"temperature": 0.1}  # low temp for factual responses
)
```

**Output:**
```json
{
  "question": "What happened in the server room last night?",
  "response": "Between 02:03 AM and 02:07 AM, ThreatLens detected a coordinated attack in the server room with a risk score of 94/100. An unauthorized person (ID #7743) entered at 02:03 AM outside permitted hours with no badge scan. 52 seconds later, an SSH login occurred from a previously unseen IP (192.168.1.157). By 02:05 AM, 847 database files were being encrypted by an unknown process. At 02:06 AM, 2.3GB of data was transferred externally. All evidence has been captured and blockchain-verified. Recommend reviewing incident INC-2024-001 immediately.",
  "supporting_incident_ids": ["INC-2024-001"],
  "evidence_links": ["/evidence/INC-2024-001/"],
  "confidence": "high"
}
```

---

## STAGE 8: Blockchain Anchoring
**Owner: P1**

**Input:**
```json
{
  "incident_id": "INC-2024-001",
  "evidence_files": [
    "/evidence/INC-2024-001/camera/clip.mp4",
    "/evidence/INC-2024-001/logs/auth_snippet.txt",
    "/evidence/INC-2024-001/network/capture.pcap",
    "/evidence/INC-2024-001/files/unknown_binary.exe"
  ]
}
```

**Processing:**
```python
from web3 import Web3
import hashlib

w3 = Web3(Web3.HTTPProvider("https://rpc-mumbai.polygon.technology"))
contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=CONTRACT_ABI)

receipts = []
for file_path in evidence_files:
    with open(file_path, "rb") as f:
        file_hash = hashlib.sha256(f.read()).hexdigest()
    
    tx = contract.functions.registerEvidence(
        bytes.fromhex(file_hash)
    ).transact({"from": wallet_address})
    
    receipt = w3.eth.wait_for_transaction_receipt(tx)
    receipts.append({
        "file": file_path,
        "sha256": file_hash,
        "tx_hash": receipt["transactionHash"].hex(),
        "block_number": receipt["blockNumber"]
    })
```

**Output (stored in MinIO + returned to dashboard):**
```json
{
  "incident_id": "INC-2024-001",
  "anchored_at": "2024-01-15T02:08:30.000Z",
  "network": "polygon-mumbai",
  "receipts": [
    {
      "file": "clip.mp4",
      "sha256": "abc123...",
      "tx_hash": "0xdeadbeef...",
      "block_number": 4821903,
      "polygonscan_url": "https://mumbai.polygonscan.com/tx/0xdeadbeef...",
      "verified": true
    }
  ],
  "chain_of_custody_intact": true,
  "legally_admissible": true
}
```

---

## Complete Model Registry

| Stage | Owner | Model | Type | Library | Training Data | Inference Time |
|-------|-------|-------|------|---------|---------------|----------------|
| 2 | P3 | EMA + Z-Score DNA | Statistical | NumPy + Redis | Live data (no training) | <1ms |
| 3A | P3 | Isolation Forest | Unsupervised ML | scikit-learn | UNSW-NB15 normal rows | <5ms |
| 3A | P3 | Autoencoder | Deep Learning | PyTorch | UNSW-NB15 normal rows | <10ms |
| 3B | P3 | Random Forest | Supervised ML | scikit-learn | Synthetic labeled logs | <5ms |
| 3B | P3 | LSTM | Deep Learning | PyTorch | Synthetic log sequences | <15ms |
| 3C | P4 | YOLOv8n | Computer Vision | Ultralytics | COCO pretrained | <30ms/frame |
| 3C | P4 | DeepSORT | Tracking | deep_sort_realtime | MOT pretrained | <10ms |
| 3D | P3 | Whitelist + Z-Score | Rule-based | Python | None | <1ms |
| 3E | P3 | Rule Engine + IF | Hybrid | scikit-learn | Normal file activity | <5ms |
| 4 | P3 | Correlation Rules | Rule-based | Python | MITRE ATT&CK rules | <10ms |
| 4 | P3 | Intent Classifier RF | Supervised ML | scikit-learn | Synthetic incidents | <5ms |
| 4 | P3 | Markov Chain Predictor | Probabilistic | Python | ATT&CK kill chain data | <1ms |
| 6 | P4 | Behavioral Rule Classifier | Rule-based | Python | None | Post-execution |
| 7A | P3 | SHAP TreeExplainer | XAI | shap library | Uses existing models | <50ms |
| 7B | P4 | NLG Template Engine | Deterministic | Python | None (templates) | <5ms |
| 7C | P4 | Mistral-7B | LLM | Ollama | Pretrained | 2-3 seconds |