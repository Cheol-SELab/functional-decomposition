# NGHE Customer Requirements (Derived from S2AF NGHE Case Study)

## 1. Purpose and scope

These customer requirements define what the Next Generation Heavy Equipment (NGHE) solution shall provide to improve **worksite productivity**, **operational effectiveness**, and **safety**, including autonomy/teleoperation capabilities and supporting services.

## 2. Stakeholders

- Site Manager
- Equipment Operator
- Tele-operator
- Safety Manager
- Maintenance/Quality
- System Engineer
- Project Manager

## 3. Customer requirements

### 3.1 Productivity and performance

- **CR-NGHE-001 (Productivity KPI)**
  - **Statement**: The NGHE solution shall support achieving the customer-defined productivity target measured in `m³/h` or `ton/h`.
  - **Acceptance criteria**: During representative operations, reported productivity is `≥ productivity_target` over the agreed evaluation period.

- **CR-NGHE-002 (Cycle time KPI)**
  - **Statement**: The NGHE solution shall support achieving the customer-defined cycle time target for the load→travel→dump cycle.
  - **Acceptance criteria**: Measured cycle time `p95 ≤ CT_target` under the agreed duty cycle and site conditions.

- **CR-NGHE-003 (Energy efficiency KPI)**
  - **Statement**: The NGHE solution shall support achieving the customer-defined energy efficiency target.
  - **Acceptance criteria**: Measured `energy_per_ton = energy_used / ton_moved` satisfies `≤ E_target` over the agreed evaluation period.

- **CR-NGHE-004 (Availability KPI)**
  - **Statement**: The NGHE solution shall meet or exceed the customer-defined operational availability target.
  - **Acceptance criteria**: Measured availability is `≥ 0.97` (or customer-defined target if different) over the agreed evaluation period.

- **CR-NGHE-005 (Performance requirement derivation)**
  - **Statement**: The NGHE solution shall provide a method to derive, record, and manage performance requirements (e.g., cycle time, energy efficiency, availability) from worksite mission context.
  - **Acceptance criteria**: The system produces a documented set of performance targets traceable to worksite inputs and maintains a history of baselines/calibration updates.

### 3.2 Worksite area analysis

- **CR-NGHE-006 (Worksite mapping/modeling)**
  - **Statement**: The NGHE solution shall provide worksite area analysis including terrain, obstacles, and work-zone representation.
  - **Acceptance criteria**: A worksite model/map is generated and available to planning/execution functions for an agreed set of site features.

- **CR-NGHE-007 (Worksite update latency)**
  - **Statement**: The NGHE solution shall update the worksite model within the customer-required timeliness for operational use.
  - **Acceptance criteria**: Worksite model update latency `p95 ≤ 1.0 s` (or customer-defined target) for supported update scenarios.

### 3.3 Autonomy and teleoperation

- **CR-NGHE-008 (Teleoperation latency)**
  - **Statement**: The NGHE solution shall support teleoperation with end-to-end communication latency compatible with safe remote operation.
  - **Acceptance criteria**: Teleoperation latency `p95 ≤ 150 ms` under the agreed network conditions.

- **CR-NGHE-009 (Teleoperation packet loss)**
  - **Statement**: The NGHE solution shall support teleoperation with communication quality meeting the customer-defined packet loss limit.
  - **Acceptance criteria**: Packet loss `≤ 1%` (or customer-defined target) under the agreed network conditions.

- **CR-NGHE-010 (Teleoperation link availability)**
  - **Statement**: The NGHE solution shall achieve the customer-defined teleoperation link availability.
  - **Acceptance criteria**: Measured link availability `≥ 0.999` (or customer-defined target) over the agreed evaluation period.

- **CR-NGHE-011 (Operational mode support)**
  - **Statement**: The NGHE solution shall support the operational modes `Manual`, `Assist`, `Autonomous`, `Teleoperation`, and `Safety Stop`.
  - **Acceptance criteria**: Each mode can be entered and exited as defined, and mode status is observable in system telemetry.

- **CR-NGHE-012 (Safe transition on degraded comms)**
  - **Statement**: The NGHE solution shall transition to a defined safe state when communication quality degrades below customer-defined thresholds.
  - **Acceptance criteria**: When `communication_quality < q_thr`, the system performs the defined safe transition (e.g., remote→local safe behavior) within the agreed response time and logs the event.

### 3.4 Safety

- **CR-NGHE-013 (Collision avoidance objective)**
  - **Statement**: The NGHE solution shall provide safety monitoring and response capabilities intended to prevent collisions during operation.
  - **Acceptance criteria**: Safety monitoring and response functions are demonstrated in representative scenarios with recorded evidence; collisions are prevented in test scenarios defined by the customer safety plan.

- **CR-NGHE-014 (Detection-to-stop time)**
  - **Statement**: The NGHE solution shall support a detection-to-stop time that meets the customer-defined safety response target.
  - **Acceptance criteria**: `detection_to_stop_time = perception_delay + control_delay + brake_delay ≤ 100 ms` (or customer-defined target) in the agreed safety scenarios.

- **CR-NGHE-015 (Emergency stop capability)**
  - **Statement**: The NGHE solution shall provide an emergency stop capability that can place equipment into a safety stop state.
  - **Acceptance criteria**: E-Stop is functional across operational modes and results in the defined safety stop behavior; reset requires an explicit recovery action per customer policy.

- **CR-NGHE-016 (Safety service latency and availability)**
  - **Statement**: The NGHE solution shall provide safety-related services meeting customer-required latency and availability.
  - **Acceptance criteria**: Safety service latency `p95 ≤ 100 ms` and availability `≥ 99.99%` (or customer-defined targets) with evidence from logs/reports.

- **CR-NGHE-017 (Operational safety business rules)**
  - **Statement**: The NGHE solution shall support operational safety rules based on environmental/operational conditions (e.g., low visibility, human detection, slope threshold).
  - **Acceptance criteria**: In configured scenarios (e.g., `visibility < θ`, `human detected`, `slope > φ_thr`), the system enforces the defined deceleration/stop/speed-limit behaviors.

### 3.5 Data exchange and interoperability

- **CR-NGHE-018 (Information exchange support)**
  - **Statement**: The NGHE solution shall support exchanging operational information including telemetry, tasking, route/plan, safety/stop signals, and maintenance alerts.
  - **Acceptance criteria**: Messages for `Map`, `Tasking`, `Route`, `Telemetry`, `SafetyAlert`, and `Maintenance` are produced/consumed as applicable in an end-to-end integration demonstration.

- **CR-NGHE-019 (Service interface support)**
  - **Statement**: The NGHE solution shall provide service interfaces suitable for integration with fleet management, edge/site systems, and equipment.
  - **Acceptance criteria**: Service endpoints are available using agreed protocols (e.g., `gRPC` and/or `REST`) and pass agreed functional integration tests.

### 3.6 Security, logging, and auditability

- **CR-NGHE-020 (Access control and control auditing)**
  - **Statement**: The NGHE solution shall support role-based access control for teleoperation/control functions and maintain control audit logs.
  - **Acceptance criteria**: RBAC policies are enforced for control actions; audit logs capture user/role, timestamp, command/action, and outcome.

- **CR-NGHE-021 (Safety/security logging integrity)**
  - **Statement**: The NGHE solution shall maintain tamper-resistant logs for safety-critical events.
  - **Acceptance criteria**: Safety event logs are generated, retained per policy, and protected to be immutable or tamper-evident per the customer’s security requirements.

- **CR-NGHE-022 (Communications security)**
  - **Statement**: The NGHE solution shall protect service communications using customer-approved encryption.
  - **Acceptance criteria**: Evidence shows encrypted communications (e.g., `TLS 1.3` for service links and configured encryption for control/safety links) per the customer security profile.

### 3.7 Verification and traceability (customer evidence)

- **CR-NGHE-023 (KPI/constraint verification evidence)**
  - **Statement**: The NGHE solution shall provide evidence that key KPI/constraint targets are verified (cycle time, energy per ton, teleoperation latency, detection-to-stop).
  - **Acceptance criteria**: A verification report exists with test cases, measured results, and pass/fail determinations for each applicable target.

- **CR-NGHE-024 (End-to-end traceability)**
  - **Statement**: The NGHE solution shall support end-to-end traceability from capabilities to operational needs, services, and resources sufficient for audit and certification activities.
  - **Acceptance criteria**: Trace links are available and reviewable for the agreed scope, and an audit can follow a chain from capability→operational activity→service→resource allocation.
