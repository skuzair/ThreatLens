EXPLANATION_TEMPLATES = {

    "camera": (
        "Unauthorized person detected in {zone} at {timestamp}. "
        "Access occurred {hours_outside} hours outside permitted window "
        "({permitted_start}-{permitted_end}). "
        "No badge scan recorded at entry point. "
        "Person tracked as ID #{reid_token}."
    ),

    "logs": (
        "SSH login from {src_ip} at {timestamp}. "
        "This IP {ip_history}. "
        "Login preceded by {failure_count} failed attempts. "
        "Privilege level escalated to {privilege_level} "
        "{time_after_login} seconds after initial login."
    ),

    "network": (
        "Outbound transfer of {transfer_size}GB to {dst_ip} at {timestamp}. "
        "Destination has {dst_history}. "
        "Transfer volume is {volume_multiple}x the baseline. "
        "Traffic pattern matches {traffic_pattern}."
    ),

    "file": (
        "{file_count} files in {directory} {modification_type} within "
        "{time_window} seconds by process {process_name} "
        "({process_status}). {extension_change_statement}."
    ),

    "correlation": (
        "All {source_count} events occurred within a "
        "{window_minutes}-minute window. "
        "Temporal sequence ({sequence}) matches "
        "{attack_pattern} attack pattern."
    ),

    "sandbox": (
        "Sandbox analysis of {filename} confirms {verdict}. "
        "File {sandbox_actions}. "
        "C2 callback attempted to {c2_domains}. "
        "{ioc_count} IOCs extracted and blacklisted."
    ),

    "prediction": (
        "Based on current attack stage ({current_stage}), "
        "system predicts {next_stage} attempt within "
        "{time_estimate} minutes (confidence: {confidence}%). "
        "Recommended action: {recommendation}."
    ),

    # DNA behavioural baseline deviation
    "dna": (
        "Behavioural baseline deviation detected for entity '{entity}'. "
        "Z-score: {zscore:.2f} (threshold: {threshold:.2f}). "
        "Anomalous features: {anomalous_features}. "
        "Deviation magnitude is {magnitude}x above normal operating range."
    ),
}