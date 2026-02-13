import { v4 as uuidv4 } from 'uuid';

const INCIDENT_TEMPLATES = [
  {
    rule_name: "Insider Data Theft",
    severity: "CRITICAL",
    sources: ["camera", "logs", "file", "network"],
    intent: "DATA_EXFILTRATION",
    zone: "Server Room",
    risk_range: [85, 98]
  },
  {
    rule_name: "Network Reconnaissance",
    severity: "HIGH",
    sources: ["network", "logs"],
    intent: "RECONNAISSANCE",
    zone: "Internal",
    risk_range: [70, 85]
  },
  {
    rule_name: "Unusual Login Pattern",
    severity: "MEDIUM",
    sources: ["logs"],
    intent: "CREDENTIAL_ABUSE",
    zone: "Lobby",
    risk_range: [50, 70]
  },
  {
    rule_name: "Rogue WiFi Device Detected",
    severity: "HIGH",
    sources: ["rf", "network"],
    intent: "RECONNAISSANCE",
    zone: "Office",
    risk_range: [75, 88]
  },
  {
    rule_name: "Mass File Encryption",
    severity: "CRITICAL",
    sources: ["file", "logs", "network"],
    intent: "MALWARE_EXECUTION",
    zone: "Data Center",
    risk_range: [90, 99]
  },
  {
    rule_name: "Suspicious Process Execution",
    severity: "HIGH",
    sources: ["logs", "file"],
    intent: "MALWARE_EXECUTION",
    zone: "Workstation",
    risk_range: [72, 86]
  },
  {
    rule_name: "Lateral Movement Detected",
    severity: "HIGH",
    sources: ["network", "logs"],
    intent: "LATERAL_MOVEMENT",
    zone: "Server Room",
    risk_range: [77, 89]
  }
];

const EVENT_DESCRIPTIONS = {
  camera: [
    "Unauthorized entry detected",
    "Person detected in restricted area",
    "No badge scan recorded",
    "After-hours presence",
    "Tailgating detected"
  ],
  logs: [
    "Failed login attempts (7x)",
    "SSH login from new IP",
    "Privilege escalation to root",
    "Suspicious command execution",
    "Account locked due to failures"
  ],
  network: [
    "Unusual outbound traffic volume",
    "Connection to unknown IP",
    "Data transfer to external destination",
    "Port scanning detected",
    "DNS tunneling activity"
  ],
  file: [
    "Mass file modification",
    "847 files encrypted",
    "Unknown binary execution",
    "Suspicious file access pattern",
    "Ransomware signature detected"
  ],
  rf: [
    "Rogue WiFi device detected",
    "Unknown MAC address",
    "Evil twin AP detected",
    "Bluetooth eavesdropping",
    "Deauth attack in progress"
  ]
};

const SOURCE_ICONS = {
  camera: "📹",
  logs: "💻",
  network: "🌐",
  file: "📁",
  rf: "📡"
};

const MITRE_TTPS = {
  DATA_EXFILTRATION: ["T1041", "T1048", "T1567"],
  RECONNAISSANCE: ["T1590", "T1595", "T1046"],
  CREDENTIAL_ABUSE: ["T1078", "T1110", "T1003"],
  MALWARE_EXECUTION: ["T1204", "T1059", "T1106"],
  LATERAL_MOVEMENT: ["T1021", "T1563", "T1570"],
  PERSISTENCE: ["T1547", "T1053", "T1543"]
};

const ATTACK_STAGES = {
  RECONNAISSANCE: "Initial Access",
  CREDENTIAL_ABUSE: "Credential Access",
  MALWARE_EXECUTION: "Execution",
  LATERAL_MOVEMENT: "Lateral Movement",
  DATA_EXFILTRATION: "Exfiltration",
  PERSISTENCE: "Persistence"
};

function randomInt(min, max) {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

function randomFloat(min, max) {
  return Math.random() * (max - min) + min;
}

function randomChoice(array) {
  return array[Math.floor(Math.random() * array.length)];
}

function generateTimestamp(minutesAgo) {
  const now = new Date();
  return new Date(now.getTime() - minutesAgo * 60000);
}

function getEventDescription(source, intent) {
  return randomChoice(EVENT_DESCRIPTIONS[source] || ["Anomaly detected"]);
}

export function generateIncident(incidentNum) {
  const template = randomChoice(INCIDENT_TEMPLATES);
  const incident_id = `INC-2024-${String(incidentNum).padStart(3, '0')}`;
  
  const minutesAgo = randomInt(5, 240);
  const timestamp = generateTimestamp(minutesAgo);
  
  const risk_score = randomInt(...template.risk_range);
  
  // Generate correlated events
  const events = [];
  const baseTime = new Date(timestamp);
  
  template.sources.forEach((source, i) => {
    const eventTime = new Date(baseTime.getTime() + i * 60000 + randomInt(0, 50) * 1000);
    events.push({
      event_id: uuidv4().substring(0, 8),
      source: source,
      timestamp: eventTime.toISOString(),
      score: randomInt(70, 95),
      description: getEventDescription(source, template.intent)
    });
  });
  
  // Generate NLG explanation
  const nlg_explanation = {
    risk_score,
    summary: `${template.severity} threat detected: ${template.rule_name}`,
    sections: events.map(event => ({
      source: event.source.toUpperCase(),
      icon: SOURCE_ICONS[event.source],
      score: event.score,
      text: `${event.description} at ${new Date(event.timestamp).toLocaleTimeString()}`
    })),
    correlation_statement: `All ${events.length} events occurred within a ${events.length * 2}-minute window, indicating coordinated attack activity.`,
    mitre_statement: `Techniques align with ${MITRE_TTPS[template.intent].join(", ")}`,
    prediction_statement: `System predicts next move within 15 minutes with 78% confidence`,
    recommended_actions: [
      "Isolate affected host immediately",
      "Block identified malicious IPs",
      "Preserve all logs for forensic analysis",
      "Notify incident response team"
    ]
  };
  
  // Predicted next move
  const predicted_next_move = {
    technique: randomChoice(["T1070", "T1486", "T1071", "T1547"]),
    name: randomChoice(["Log Deletion", "Data Encryption", "C2 Communication", "Persistence"]),
    confidence: randomFloat(0.7, 0.95),
    time_estimate_minutes: randomInt(5, 20)
  };
  
  return {
    incident_id,
    timestamp: timestamp.toISOString(),
    risk_score,
    severity: template.severity,
    rule_name: template.rule_name,
    sources_involved: template.sources,
    correlated_events: events,
    intent_primary: template.intent,
    intent_confidence: randomFloat(0.75, 0.98),
    mitre_ttps: MITRE_TTPS[template.intent].slice(0, 2),
    current_attack_stage: ATTACK_STAGES[template.intent],
    predicted_next_move,
    nlg_explanation,
    status: "open",
    zone: template.zone
  };
}

export function generateMultipleIncidents(count = 10) {
  return Array.from({ length: count }, (_, i) => generateIncident(i + 1));
}

export function generateSandboxResult(incident_id) {
  const verdicts = ["MALICIOUS", "SUSPICIOUS", "BENIGN"];
  const verdict = randomChoice(verdicts);
  const confidence_score = verdict === "MALICIOUS" ? randomInt(85, 99) : randomInt(60, 84);
  
  return {
    result_id: uuidv4().substring(0, 8),
    incident_id,
    file_hash: "sha256:" + Array(64).fill(0).map(() => 
      Math.floor(Math.random() * 16).toString(16)).join(''),
    verdict,
    confidence_score,
    behavioral_summary: {
      files_encrypted: 847,
      ransom_note_created: "C:/ransom_note.txt",
      shadow_copies_deleted: true,
      c2_callback: "evil-c2.ru:443",
      persistence_added: "HKCU\\Run\\persist_malware"
    },
    extracted_iocs: {
      ips: ["203.0.113.5", "198.51.100.3"],
      domains: ["evil-c2.ru", "malware-cdn.com"],
      hashes: [
        "sha256:deadbeef" + "0".repeat(56),
        "sha256:cafebabe" + "0".repeat(56)
      ],
      registry_keys: ["HKCU\\Run\\persist_malware"],
      mitre_behaviors: ["T1486", "T1490", "T1071", "T1547"]
    },
    screenshot_count: 60,
    mitre_behaviors: ["T1486", "T1490", "T1071", "T1547"],
    detonation_timestamp: new Date().toISOString()
  };
}

export function generateEvidence(incident_id, sources) {
  return sources.map((source, i) => ({
    evidence_id: uuidv4().substring(0, 8),
    incident_id,
    capture_timestamp: new Date().toISOString(),
    evidence_type: source === 'camera' ? 'video' : source === 'network' ? 'pcap' : 'logs',
    file_path: `/evidence/${incident_id}/${source}_${i}.${source === 'camera' ? 'mp4' : 'txt'}`,
    sha256_hash: "sha256:" + Array(64).fill(0).map(() => 
      Math.floor(Math.random() * 16).toString(16)).join(''),
    blockchain_tx_hash: "0x" + Array(64).fill(0).map(() => 
      Math.floor(Math.random() * 16).toString(16)).join(''),
    blockchain_block_number: randomInt(4821900, 4821950),
    verified: true,
    metadata: {
      size_bytes: randomInt(1000000, 50000000),
      duration_seconds: source === 'camera' ? randomInt(10, 60) : null
    }
  }));
}

export function generateIOCs(incident_id) {
  const iocs = [];
  
  // IP addresses
  for (let i = 0; i < randomInt(2, 5); i++) {
    iocs.push({
      ioc_id: uuidv4().substring(0, 8),
      incident_id,
      ioc_type: 'ip',
      value: `${randomInt(1, 255)}.${randomInt(0, 255)}.${randomInt(0, 255)}.${randomInt(0, 255)}`,
      confidence: randomFloat(0.7, 0.99),
      source: 'sandbox',
      first_seen: new Date().toISOString(),
      times_seen: randomInt(1, 10),
      blocked: false
    });
  }
  
  // Domains
  const maliciousDomains = ['evil-c2.ru', 'malware-cdn.com', 'phishing-site.net'];
  iocs.push({
    ioc_id: uuidv4().substring(0, 8),
    incident_id,
    ioc_type: 'domain',
    value: randomChoice(maliciousDomains),
    confidence: randomFloat(0.85, 0.99),
    source: 'sandbox',
    first_seen: new Date().toISOString(),
    times_seen: randomInt(3, 15),
    blocked: false
  });
  
  return iocs;
}
