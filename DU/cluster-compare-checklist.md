# Telco RAN DU vs cluster-compare (release-4.20 reference)

Source: `cluster-compare-report.json` (same run as the full text report).


## Summary

- **Metadata hash:** `701a9f29a26217c217deb3d8b1a31905792e52cb254d302c8c3b13f2e588f7ca`
- **Total CRs compared:** 85
- **Missing template matches (validation):** 28
- **Resources with diffs:** 36
- **Unmatched cluster CRs:** 0
- **Patched / user overrides applied:** 0

## Missing or not satisfied (by reference part)

### `optional-image-registry`

- **image-registry** — Missing CRs

  - `image-registry/ImageRegistryPV.yaml`

### `optional-ptp-config`

- **ptp-config** — One of the following is required

  - `ptp-operator/configuration/PtpConfigGnrdTGM.yaml`
  - `ptp-operator/configuration/PtpConfigGnrdBcNoHoldover.yaml`
  - `ptp-operator/configuration/PtpConfigBoundary.yaml`
  - `ptp-operator/configuration/PtpConfigGmWpc.yaml`
  - `ptp-operator/configuration/PtpConfigDualCardGmWpc.yaml`
  - `ptp-operator/configuration/PtpConfigDualFollower.yaml`
  - `ptp-operator/configuration/PtpConfigThreeCardGmWpc.yaml`
  - `ptp-operator/configuration/PtpConfigForHA.yaml`
  - `ptp-operator/configuration/PtpConfigMaster.yaml`
  - `ptp-operator/configuration/PtpConfigSlave.yaml`
  - `ptp-operator/configuration/PtpConfigSlaveForEvent.yaml`
  - `ptp-operator/configuration/PtpConfigForHAForEvent.yaml`
  - `ptp-operator/configuration/PtpConfigMasterForEvent.yaml`
  - `ptp-operator/configuration/PtpConfigBoundaryForEvent.yaml`
- **ptp-operator-config** — One of the following is required

  - `ptp-operator/configuration/PtpOperatorConfig.yaml`
  - `ptp-operator/configuration/PtpOperatorConfigForEvent.yaml`

### `optional-storage`

- **storage** — Missing CRs

  - `storage/StorageLV.yaml`

### `optional-storage-lvm`

- **storage-operator** — Missing CRs

  - `storage-lvm/StorageLVMCluster.yaml`
  - `storage-lvm/StorageLVMSubscriptionOperGroup.yaml`
  - `storage-lvm/StoragePV.yaml`

### `required-cluster-logging`

- **cluster-logging** — Missing CRs

  - `cluster-logging/ClusterLogNS.yaml`
  - `cluster-logging/ClusterLogOperGroup.yaml`
  - `cluster-logging/ClusterLogSubscription.yaml`
  - `cluster-logging/ClusterLogForwarder.yaml`
  - `cluster-logging/ClusterLogServiceAccount.yaml`
  - `cluster-logging/ClusterLogServiceAccountAuditBinding.yaml`
  - `cluster-logging/ClusterLogServiceAccountInfrastructureBinding.yaml`

### `required-cluster-tuning`

- **cluster-tuning** — Missing CRs

  - `cluster-tuning/operator-hub/DefaultCatsrc.yaml`

### `required-machine-config`

- **machine-config** — Missing CRs

  - `machine-config/disable-crio-wipe/99-crio-disable-wipe-worker.yaml`
  - `machine-config/one-shot-time-sync/99-sync-time-once-master.yaml`
  - `machine-config/one-shot-time-sync/99-sync-time-once-worker.yaml`
  - `machine-config/sctp/03-sctp-machine-config-master.yaml`
  - `machine-config/sctp/03-sctp-machine-config-worker.yaml`
  - `machine-config/sriov-related-kernel-arguments/07-sriov-related-kernel-args-master.yaml`
  - `machine-config/sriov-related-kernel-arguments/07-sriov-related-kernel-args-worker.yaml`
  - `machine-config/crun/enable-crun-master.yaml`
  - `machine-config/crun/enable-crun-worker.yaml`
  - `machine-config/rename-gnrd-interfaces/10-rename-gnrd-interfaces-master.yaml`
  - `machine-config/rename-gnrd-interfaces/10-rename-gnrd-interfaces-worker.yaml`

### `required-node-tuning-operator`

- **node-tuning-operator** — Missing CRs

  - `node-tuning-operator/PerformanceProfile.yaml`
  - `node-tuning-operator/TunedPerformancePatch.yaml`


## Notable diffs (non-empty diff text only)

These are material field-level differences, not just “matched, no diff output”.

### imageregistry.operator.openshift.io/v1_Config_cluster

- **Template:** `image-registry/ImageRegistryConfig.yaml`
- **Note:** https://docs.openshift.com/container-platform/4.20/scalability_and_performance/telco_ref_design_specs/ran/telco-ran-ref-du-components.html#telco-ran-lca-operator_ran-ref-design-components

```diff
diff -u -N /tmp/MERGED-2920599164/imageregistry-operator-openshift-io-v1_config_cluster /tmp/LIVE-1565714982/imageregistry-operator-openshift-io-v1_config_cluster
--- /tmp/MERGED-2920599164/imageregistry-operator-openshift-io-v1_config_cluster	2026-04-28 10:47:32.098441603 -0400
+++ /tmp/LIVE-1565714982/imageregistry-operator-openshift-io-v1_config_cluster	2026-04-28 10:47:32.098441603 -0400
@@ -4,15 +4,16 @@
   name: cluster
 spec:
   logLevel: Normal
-  managementState: Managed
+  managementState: Removed
   observedConfig: null
   operatorLogLevel: Normal
+  proxy: {}
   replicas: 1
   requests:
     read:
       maxWaitInQueue: 0s
     write:
       maxWaitInQueue: 0s
... (truncated)
```

### machineconfiguration.openshift.io/v1_MachineConfig_06-kdump-enable-master

- **Template:** `machine-config/kdump/06-kdump-master.yaml`
- **Note:** https://docs.openshift.com/container-platform/4.20/scalability_and_performance/telco_ref_design_specs/ran/telco-ran-ref-du-components.html#telco-ran-machine-configuration_ran-ref-design-components

```diff
diff -u -N /tmp/MERGED-2228254977/machineconfiguration-openshift-io-v1_machineconfig_06-kdump-enable-master /tmp/LIVE-61931787/machineconfiguration-openshift-io-v1_machineconfig_06-kdump-enable-master
--- /tmp/MERGED-2228254977/machineconfiguration-openshift-io-v1_machineconfig_06-kdump-enable-master	2026-04-28 10:47:32.100441592 -0400
+++ /tmp/LIVE-61931787/machineconfiguration-openshift-io-v1_machineconfig_06-kdump-enable-master	2026-04-28 10:47:32.100441592 -0400
@@ -13,4 +13,4 @@
       - enabled: true
         name: kdump.service
   kernelArguments:
-  - crashkernel=676M
+  - crashkernel=512M
```

### machineconfiguration.openshift.io/v1_MachineConfig_06-kdump-enable-worker

- **Template:** `machine-config/kdump/06-kdump-worker.yaml`
- **Note:** https://docs.openshift.com/container-platform/4.20/scalability_and_performance/telco_ref_design_specs/ran/telco-ran-ref-du-components.html#telco-ran-machine-configuration_ran-ref-design-components

```diff
diff -u -N /tmp/MERGED-2881802099/machineconfiguration-openshift-io-v1_machineconfig_06-kdump-enable-worker /tmp/LIVE-115566815/machineconfiguration-openshift-io-v1_machineconfig_06-kdump-enable-worker
--- /tmp/MERGED-2881802099/machineconfiguration-openshift-io-v1_machineconfig_06-kdump-enable-worker	2026-04-28 10:47:32.102441582 -0400
+++ /tmp/LIVE-115566815/machineconfiguration-openshift-io-v1_machineconfig_06-kdump-enable-worker	2026-04-28 10:47:32.102441582 -0400
@@ -13,4 +13,4 @@
       - enabled: true
         name: kdump.service
   kernelArguments:
-  - crashkernel=676M
+  - crashkernel=512M
```

### machineconfiguration.openshift.io/v1_MachineConfig_container-mount-namespace-and-kubelet-conf-master

- **Template:** `machine-config/kubelet-configuration-and-container-mount-hiding/01-container-mount-ns-and-kubelet-conf-master.yaml`
- **Note:** https://docs.openshift.com/container-platform/4.20/scalability_and_performance/telco_ref_design_specs/ran/telco-ran-ref-du-components.html#telco-ran-machine-configuration_ran-ref-design-components

```diff
diff -u -N /tmp/MERGED-2773369382/machineconfiguration-openshift-io-v1_machineconfig_container-mount-namespace-and-kubelet-conf-master /tmp/LIVE-1135242992/machineconfiguration-openshift-io-v1_machineconfig_container-mount-namespace-and-kubelet-conf-master
--- /tmp/MERGED-2773369382/machineconfiguration-openshift-io-v1_machineconfig_container-mount-namespace-and-kubelet-conf-master	2026-04-28 10:47:32.114441517 -0400
+++ /tmp/LIVE-1135242992/machineconfiguration-openshift-io-v1_machineconfig_container-mount-namespace-and-kubelet-conf-master	2026-04-28 10:47:32.114441517 -0400
@@ -34,6 +34,7 @@
           ExecStartPre=touch ${BIND_POINT}
           ExecStart=unshare --mount=${BIND_POINT} --propagation slave mount --make-rshared /
           ExecStop=umount -R ${RUNTIME_DIRECTORY}
+        enabled: true
         name: container-mount-namespace.service
       - dropins:
         - contents: |
```

### operator.openshift.io/v1_Console_cluster

- **Template:** `cluster-tuning/console-disable/ConsoleOperatorDisable.yaml`
- **Note:** https://docs.openshift.com/container-platform/4.20/scalability_and_performance/telco_ref_design_specs/ran/telco-ran-ref-du-components.html#telco-ran-cluster-tuning_ran-ref-design-components

```diff
diff -u -N /tmp/MERGED-4111049250/operator-openshift-io-v1_console_cluster /tmp/LIVE-3235312736/operator-openshift-io-v1_console_cluster
--- /tmp/MERGED-4111049250/operator-openshift-io-v1_console_cluster	2026-04-28 10:47:32.119441490 -0400
+++ /tmp/LIVE-3235312736/operator-openshift-io-v1_console_cluster	2026-04-28 10:47:32.119441490 -0400
@@ -3,6 +3,39 @@
 metadata:
   name: cluster
 spec:
+  customization:
+    addPage: {}
+    capabilities:
+    - name: LightspeedButton
+      visibility:
+        state: Enabled
+    - name: GettingStartedBanner
+      visibility:
+        state: Enabled
+    customLogoFile:
+      name: ""
... (truncated)
```

### v1_ConfigMap_openshift-monitoring_cluster-monitoring-config

- **Template:** `cluster-tuning/monitoring-configuration/ReduceMonitoringFootprint.yaml`
- **Note:** https://docs.openshift.com/container-platform/4.20/scalability_and_performance/telco_ref_design_specs/ran/telco-ran-ref-du-components.html#telco-ran-cluster-tuning_ran-ref-design-components

```diff
diff -u -N /tmp/MERGED-471377179/v1_configmap_openshift-monitoring_cluster-monitoring-config /tmp/LIVE-2534713580/v1_configmap_openshift-monitoring_cluster-monitoring-config
--- /tmp/MERGED-471377179/v1_configmap_openshift-monitoring_cluster-monitoring-config	2026-04-28 10:47:32.134441409 -0400
+++ /tmp/LIVE-2534713580/v1_configmap_openshift-monitoring_cluster-monitoring-config	2026-04-28 10:47:32.134441409 -0400
@@ -5,33 +5,8 @@
       enabled: false
     telemeterClient:
       enabled: false
-    nodeExporter:
-      collectors:
-        buddyinfo: {}
-        cpufreq: {}
-        ksmd: {}
-        mountstats: {}
-        netclass: {}
-        netdev: {}
-        processes: {}
-        systemd: {}
-        tcpstat: {}
... (truncated)
```

### v1_Namespace_openshift-ptp

- **Template:** `ptp-operator/PtpSubscriptionNS.yaml`
- **Note:** https://docs.openshift.com/container-platform/4.20/scalability_and_performance/telco_ref_design_specs/ran/telco-ran-ref-du-components.html#telco-ran-ptp-operator_ran-ref-design-components

```diff
diff -u -N /tmp/MERGED-271121669/v1_namespace_openshift-ptp /tmp/LIVE-2931614195/v1_namespace_openshift-ptp
--- /tmp/MERGED-271121669/v1_namespace_openshift-ptp	2026-04-28 10:47:32.136441398 -0400
+++ /tmp/LIVE-2931614195/v1_namespace_openshift-ptp	2026-04-28 10:47:32.136441398 -0400
@@ -4,5 +4,6 @@
   annotations:
     workload.openshift.io/allowed: management
   labels:
+    name: openshift-ptp
     openshift.io/cluster-monitoring: "true"
   name: openshift-ptp
```

### sriovnetwork.openshift.io/v1_SriovNetworkNodePolicy_openshift-sriov-network-operator_policy-ca

- **Template:** `sriov-operator/SriovNetworkNodePolicy.yaml`
- **Note:** https://docs.openshift.com/container-platform/4.20/scalability_and_performance/telco_ref_design_specs/ran/telco-ran-ref-du-components.html#telco-ran-sr-iov-operator_ran-ref-design-components

```diff
diff -u -N /tmp/MERGED-3226998848/sriovnetwork-openshift-io-v1_sriovnetworknodepolicy_openshift-sriov-network-operator_policy-ca /tmp/LIVE-2619012458/sriovnetwork-openshift-io-v1_sriovnetworknodepolicy_openshift-sriov-network-operator_policy-ca
--- /tmp/MERGED-3226998848/sriovnetwork-openshift-io-v1_sriovnetworknodepolicy_openshift-sriov-network-operator_policy-ca	2026-04-28 10:47:32.149441328 -0400
+++ /tmp/LIVE-2619012458/sriovnetwork-openshift-io-v1_sriovnetworknodepolicy_openshift-sriov-network-operator_policy-ca	2026-04-28 10:47:32.149441328 -0400
@@ -12,7 +12,7 @@
     - ens14f1#0-7
     vendor: "8086"
   nodeSelector:
-    node-role.kubernetes.io/.*: Prefix must match
+    feature.node.kubernetes.io/network-sriov.capable: "true"
   numVfs: 8
   priority: 99
   resourceName: pci_sriov_net_ca
```

### sriovnetwork.openshift.io/v1_SriovNetworkNodePolicy_openshift-sriov-network-operator_policy-f1c

- **Template:** `sriov-operator/SriovNetworkNodePolicy.yaml`
- **Note:** https://docs.openshift.com/container-platform/4.20/scalability_and_performance/telco_ref_design_specs/ran/telco-ran-ref-du-components.html#telco-ran-sr-iov-operator_ran-ref-design-components

```diff
diff -u -N /tmp/MERGED-2053183459/sriovnetwork-openshift-io-v1_sriovnetworknodepolicy_openshift-sriov-network-operator_policy-f1c /tmp/LIVE-2087498521/sriovnetwork-openshift-io-v1_sriovnetworknodepolicy_openshift-sriov-network-operator_policy-f1c
--- /tmp/MERGED-2053183459/sriovnetwork-openshift-io-v1_sriovnetworknodepolicy_openshift-sriov-network-operator_policy-f1c	2026-04-28 10:47:32.152441311 -0400
+++ /tmp/LIVE-2087498521/sriovnetwork-openshift-io-v1_sriovnetworknodepolicy_openshift-sriov-network-operator_policy-f1c	2026-04-28 10:47:32.152441311 -0400
@@ -12,7 +12,7 @@
     - ens14f0#0-5
     vendor: "8086"
   nodeSelector:
-    node-role.kubernetes.io/.*: Prefix must match
+    feature.node.kubernetes.io/network-sriov.capable: "true"
   numVfs: 8
   priority: 99
   resourceName: pci_sriov_net_f1c
```

### sriovnetwork.openshift.io/v1_SriovNetworkNodePolicy_openshift-sriov-network-operator_policy-f1u

- **Template:** `sriov-operator/SriovNetworkNodePolicy.yaml`
- **Note:** https://docs.openshift.com/container-platform/4.20/scalability_and_performance/telco_ref_design_specs/ran/telco-ran-ref-du-components.html#telco-ran-sr-iov-operator_ran-ref-design-components

```diff
diff -u -N /tmp/MERGED-1683450769/sriovnetwork-openshift-io-v1_sriovnetworknodepolicy_openshift-sriov-network-operator_policy-f1u /tmp/LIVE-3238938493/sriovnetwork-openshift-io-v1_sriovnetworknodepolicy_openshift-sriov-network-operator_policy-f1u
--- /tmp/MERGED-1683450769/sriovnetwork-openshift-io-v1_sriovnetworknodepolicy_openshift-sriov-network-operator_policy-f1u	2026-04-28 10:47:32.154441300 -0400
+++ /tmp/LIVE-3238938493/sriovnetwork-openshift-io-v1_sriovnetworknodepolicy_openshift-sriov-network-operator_policy-f1u	2026-04-28 10:47:32.154441300 -0400
@@ -12,7 +12,7 @@
     - ens14f0#6-7
     vendor: "8086"
   nodeSelector:
-    node-role.kubernetes.io/.*: Prefix must match
+    feature.node.kubernetes.io/network-sriov.capable: "true"
   numVfs: 8
   priority: 99
   resourceName: pci_sriov_net_f1u
```

### sriovnetwork.openshift.io/v1_SriovNetworkNodePolicy_openshift-sriov-network-operator_policy-fh0

- **Template:** `sriov-operator/SriovNetworkNodePolicy.yaml`
- **Note:** https://docs.openshift.com/container-platform/4.20/scalability_and_performance/telco_ref_design_specs/ran/telco-ran-ref-du-components.html#telco-ran-sr-iov-operator_ran-ref-design-components

```diff
diff -u -N /tmp/MERGED-3673618003/sriovnetwork-openshift-io-v1_sriovnetworknodepolicy_openshift-sriov-network-operator_policy-fh0 /tmp/LIVE-3716005387/sriovnetwork-openshift-io-v1_sriovnetworknodepolicy_openshift-sriov-network-operator_policy-fh0
--- /tmp/MERGED-3673618003/sriovnetwork-openshift-io-v1_sriovnetworknodepolicy_openshift-sriov-network-operator_policy-fh0	2026-04-28 10:47:32.157441284 -0400
+++ /tmp/LIVE-3716005387/sriovnetwork-openshift-io-v1_sriovnetworknodepolicy_openshift-sriov-network-operator_policy-fh0	2026-04-28 10:47:32.157441284 -0400
@@ -12,7 +12,7 @@
     - ens1f0#4-7
     vendor: "8086"
   nodeSelector:
-    node-role.kubernetes.io/.*: Prefix must match
+    feature.node.kubernetes.io/network-sriov.capable: "true"
   numVfs: 8
   priority: 99
   resourceName: pci_sriov_net_fh0
```

### sriovnetwork.openshift.io/v1_SriovNetworkNodePolicy_openshift-sriov-network-operator_policy-fh0m

- **Template:** `sriov-operator/SriovNetworkNodePolicy.yaml`
- **Note:** https://docs.openshift.com/container-platform/4.20/scalability_and_performance/telco_ref_design_specs/ran/telco-ran-ref-du-components.html#telco-ran-sr-iov-operator_ran-ref-design-components

```diff
diff -u -N /tmp/MERGED-2331145118/sriovnetwork-openshift-io-v1_sriovnetworknodepolicy_openshift-sriov-network-operator_policy-fh0m /tmp/LIVE-3266552617/sriovnetwork-openshift-io-v1_sriovnetworknodepolicy_openshift-sriov-network-operator_policy-fh0m
--- /tmp/MERGED-2331145118/sriovnetwork-openshift-io-v1_sriovnetworknodepolicy_openshift-sriov-network-operator_policy-fh0m	2026-04-28 10:47:32.159441273 -0400
+++ /tmp/LIVE-3266552617/sriovnetwork-openshift-io-v1_sriovnetworknodepolicy_openshift-sriov-network-operator_policy-fh0m	2026-04-28 10:47:32.159441273 -0400
@@ -12,7 +12,7 @@
     - ens1f0#0-3
     vendor: "8086"
   nodeSelector:
-    node-role.kubernetes.io/.*: Prefix must match
+    feature.node.kubernetes.io/network-sriov.capable: "true"
   numVfs: 8
   priority: 99
   resourceName: pci_sriov_net_fh0m
```

### sriovnetwork.openshift.io/v1_SriovNetworkNodePolicy_openshift-sriov-network-operator_policy-fh1

- **Template:** `sriov-operator/SriovNetworkNodePolicy.yaml`
- **Note:** https://docs.openshift.com/container-platform/4.20/scalability_and_performance/telco_ref_design_specs/ran/telco-ran-ref-du-components.html#telco-ran-sr-iov-operator_ran-ref-design-components

```diff
diff -u -N /tmp/MERGED-670592652/sriovnetwork-openshift-io-v1_sriovnetworknodepolicy_openshift-sriov-network-operator_policy-fh1 /tmp/LIVE-1449976183/sriovnetwork-openshift-io-v1_sriovnetworknodepolicy_openshift-sriov-network-operator_policy-fh1
--- /tmp/MERGED-670592652/sriovnetwork-openshift-io-v1_sriovnetworknodepolicy_openshift-sriov-network-operator_policy-fh1	2026-04-28 10:47:32.161441263 -0400
+++ /tmp/LIVE-1449976183/sriovnetwork-openshift-io-v1_sriovnetworknodepolicy_openshift-sriov-network-operator_policy-fh1	2026-04-28 10:47:32.161441263 -0400
@@ -12,7 +12,7 @@
     - ens1f1#4-7
     vendor: "8086"
   nodeSelector:
-    node-role.kubernetes.io/.*: Prefix must match
+    feature.node.kubernetes.io/network-sriov.capable: "true"
   numVfs: 8
   priority: 99
   resourceName: pci_sriov_net_fh1
```

### sriovnetwork.openshift.io/v1_SriovNetworkNodePolicy_openshift-sriov-network-operator_policy-fh10

- **Template:** `sriov-operator/SriovNetworkNodePolicy.yaml`
- **Note:** https://docs.openshift.com/container-platform/4.20/scalability_and_performance/telco_ref_design_specs/ran/telco-ran-ref-du-components.html#telco-ran-sr-iov-operator_ran-ref-design-components

```diff
diff -u -N /tmp/MERGED-2397546742/sriovnetwork-openshift-io-v1_sriovnetworknodepolicy_openshift-sriov-network-operator_policy-fh10 /tmp/LIVE-2403536987/sriovnetwork-openshift-io-v1_sriovnetworknodepolicy_openshift-sriov-network-operator_policy-fh10
--- /tmp/MERGED-2397546742/sriovnetwork-openshift-io-v1_sriovnetworknodepolicy_openshift-sriov-network-operator_policy-fh10	2026-04-28 10:47:32.163441251 -0400
+++ /tmp/LIVE-2403536987/sriovnetwork-openshift-io-v1_sriovnetworknodepolicy_openshift-sriov-network-operator_policy-fh10	2026-04-28 10:47:32.163441251 -0400
@@ -12,7 +12,7 @@
     - ens3f2#4-7
     vendor: "8086"
   nodeSelector:
-    node-role.kubernetes.io/.*: Prefix must match
+    feature.node.kubernetes.io/network-sriov.capable: "true"
   numVfs: 8
   priority: 99
   resourceName: pci_sriov_net_fh10
```

### sriovnetwork.openshift.io/v1_SriovNetworkNodePolicy_openshift-sriov-network-operator_policy-fh10m

- **Template:** `sriov-operator/SriovNetworkNodePolicy.yaml`
- **Note:** https://docs.openshift.com/container-platform/4.20/scalability_and_performance/telco_ref_design_specs/ran/telco-ran-ref-du-components.html#telco-ran-sr-iov-operator_ran-ref-design-components

```diff
diff -u -N /tmp/MERGED-665615306/sriovnetwork-openshift-io-v1_sriovnetworknodepolicy_openshift-sriov-network-operator_policy-fh10m /tmp/LIVE-2492695729/sriovnetwork-openshift-io-v1_sriovnetworknodepolicy_openshift-sriov-network-operator_policy-fh10m
--- /tmp/MERGED-665615306/sriovnetwork-openshift-io-v1_sriovnetworknodepolicy_openshift-sriov-network-operator_policy-fh10m	2026-04-28 10:47:32.166441235 -0400
+++ /tmp/LIVE-2492695729/sriovnetwork-openshift-io-v1_sriovnetworknodepolicy_openshift-sriov-network-operator_policy-fh10m	2026-04-28 10:47:32.166441235 -0400
@@ -12,7 +12,7 @@
     - ens3f2#0-3
     vendor: "8086"
   nodeSelector:
-    node-role.kubernetes.io/.*: Prefix must match
+    feature.node.kubernetes.io/network-sriov.capable: "true"
   numVfs: 8
   priority: 99
   resourceName: pci_sriov_net_fh10m
```

### sriovnetwork.openshift.io/v1_SriovNetworkNodePolicy_openshift-sriov-network-operator_policy-fh11

- **Template:** `sriov-operator/SriovNetworkNodePolicy.yaml`
- **Note:** https://docs.openshift.com/container-platform/4.20/scalability_and_performance/telco_ref_design_specs/ran/telco-ran-ref-du-components.html#telco-ran-sr-iov-operator_ran-ref-design-components

```diff
diff -u -N /tmp/MERGED-2426736155/sriovnetwork-openshift-io-v1_sriovnetworknodepolicy_openshift-sriov-network-operator_policy-fh11 /tmp/LIVE-2002135392/sriovnetwork-openshift-io-v1_sriovnetworknodepolicy_openshift-sriov-network-operator_policy-fh11
--- /tmp/MERGED-2426736155/sriovnetwork-openshift-io-v1_sriovnetworknodepolicy_openshift-sriov-network-operator_policy-fh11	2026-04-28 10:47:32.168441224 -0400
+++ /tmp/LIVE-2002135392/sriovnetwork-openshift-io-v1_sriovnetworknodepolicy_openshift-sriov-network-operator_policy-fh11	2026-04-28 10:47:32.168441224 -0400
@@ -12,7 +12,7 @@
     - ens3f3#4-7
     vendor: "8086"
   nodeSelector:
-    node-role.kubernetes.io/.*: Prefix must match
+    feature.node.kubernetes.io/network-sriov.capable: "true"
   numVfs: 8
   priority: 99
   resourceName: pci_sriov_net_fh11
```

### sriovnetwork.openshift.io/v1_SriovNetworkNodePolicy_openshift-sriov-network-operator_policy-fh11m

- **Template:** `sriov-operator/SriovNetworkNodePolicy.yaml`
- **Note:** https://docs.openshift.com/container-platform/4.20/scalability_and_performance/telco_ref_design_specs/ran/telco-ran-ref-du-components.html#telco-ran-sr-iov-operator_ran-ref-design-components

```diff
diff -u -N /tmp/MERGED-911484334/sriovnetwork-openshift-io-v1_sriovnetworknodepolicy_openshift-sriov-network-operator_policy-fh11m /tmp/LIVE-741428172/sriovnetwork-openshift-io-v1_sriovnetworknodepolicy_openshift-sriov-network-operator_policy-fh11m
--- /tmp/MERGED-911484334/sriovnetwork-openshift-io-v1_sriovnetworknodepolicy_openshift-sriov-network-operator_policy-fh11m	2026-04-28 10:47:32.170441214 -0400
+++ /tmp/LIVE-741428172/sriovnetwork-openshift-io-v1_sriovnetworknodepolicy_openshift-sriov-network-operator_policy-fh11m	2026-04-28 10:47:32.171441208 -0400
@@ -12,7 +12,7 @@
     - ens3f3#0-3
     vendor: "8086"
   nodeSelector:
-    node-role.kubernetes.io/.*: Prefix must match
+    feature.node.kubernetes.io/network-sriov.capable: "true"
   numVfs: 8
   priority: 99
   resourceName: pci_sriov_net_fh11m
```

### sriovnetwork.openshift.io/v1_SriovNetworkNodePolicy_openshift-sriov-network-operator_policy-fh1m

- **Template:** `sriov-operator/SriovNetworkNodePolicy.yaml`
- **Note:** https://docs.openshift.com/container-platform/4.20/scalability_and_performance/telco_ref_design_specs/ran/telco-ran-ref-du-components.html#telco-ran-sr-iov-operator_ran-ref-design-components

```diff
diff -u -N /tmp/MERGED-3771690874/sriovnetwork-openshift-io-v1_sriovnetworknodepolicy_openshift-sriov-network-operator_policy-fh1m /tmp/LIVE-3160004722/sriovnetwork-openshift-io-v1_sriovnetworknodepolicy_openshift-sriov-network-operator_policy-fh1m
--- /tmp/MERGED-3771690874/sriovnetwork-openshift-io-v1_sriovnetworknodepolicy_openshift-sriov-network-operator_policy-fh1m	2026-04-28 10:47:32.174441192 -0400
+++ /tmp/LIVE-3160004722/sriovnetwork-openshift-io-v1_sriovnetworknodepolicy_openshift-sriov-network-operator_policy-fh1m	2026-04-28 10:47:32.174441192 -0400
@@ -12,7 +12,7 @@
     - ens1f1#0-3
     vendor: "8086"
   nodeSelector:
-    node-role.kubernetes.io/.*: Prefix must match
+    feature.node.kubernetes.io/network-sriov.capable: "true"
   numVfs: 8
   priority: 99
   resourceName: pci_sriov_net_fh1m
```

### sriovnetwork.openshift.io/v1_SriovNetworkNodePolicy_openshift-sriov-network-operator_policy-fh2

- **Template:** `sriov-operator/SriovNetworkNodePolicy.yaml`
- **Note:** https://docs.openshift.com/container-platform/4.20/scalability_and_performance/telco_ref_design_specs/ran/telco-ran-ref-du-components.html#telco-ran-sr-iov-operator_ran-ref-design-components

```diff
diff -u -N /tmp/MERGED-4119099743/sriovnetwork-openshift-io-v1_sriovnetworknodepolicy_openshift-sriov-network-operator_policy-fh2 /tmp/LIVE-97906512/sriovnetwork-openshift-io-v1_sriovnetworknodepolicy_openshift-sriov-network-operator_policy-fh2
--- /tmp/MERGED-4119099743/sriovnetwork-openshift-io-v1_sriovnetworknodepolicy_openshift-sriov-network-operator_policy-fh2	2026-04-28 10:47:32.176441181 -0400
+++ /tmp/LIVE-97906512/sriovnetwork-openshift-io-v1_sriovnetworknodepolicy_openshift-sriov-network-operator_policy-fh2	2026-04-28 10:47:32.176441181 -0400
@@ -12,7 +12,7 @@
     - ens1f2#4-7
     vendor: "8086"
   nodeSelector:
-    node-role.kubernetes.io/.*: Prefix must match
+    feature.node.kubernetes.io/network-sriov.capable: "true"
   numVfs: 8
   priority: 99
   resourceName: pci_sriov_net_fh2
```

### sriovnetwork.openshift.io/v1_SriovNetworkNodePolicy_openshift-sriov-network-operator_policy-fh2m

- **Template:** `sriov-operator/SriovNetworkNodePolicy.yaml`
- **Note:** https://docs.openshift.com/container-platform/4.20/scalability_and_performance/telco_ref_design_specs/ran/telco-ran-ref-du-components.html#telco-ran-sr-iov-operator_ran-ref-design-components

```diff
diff -u -N /tmp/MERGED-2621350934/sriovnetwork-openshift-io-v1_sriovnetworknodepolicy_openshift-sriov-network-operator_policy-fh2m /tmp/LIVE-939533925/sriovnetwork-openshift-io-v1_sriovnetworknodepolicy_openshift-sriov-network-operator_policy-fh2m
--- /tmp/MERGED-2621350934/sriovnetwork-openshift-io-v1_sriovnetworknodepolicy_openshift-sriov-network-operator_policy-fh2m	2026-04-28 10:47:32.177441176 -0400
+++ /tmp/LIVE-939533925/sriovnetwork-openshift-io-v1_sriovnetworknodepolicy_openshift-sriov-network-operator_policy-fh2m	2026-04-28 10:47:32.177441176 -0400
@@ -12,7 +12,7 @@
     - ens1f2#0-3
     vendor: "8086"
   nodeSelector:
-    node-role.kubernetes.io/.*: Prefix must match
+    feature.node.kubernetes.io/network-sriov.capable: "true"
   numVfs: 8
   priority: 99
   resourceName: pci_sriov_net_fh2m
```

### sriovnetwork.openshift.io/v1_SriovNetworkNodePolicy_openshift-sriov-network-operator_policy-fh3

- **Template:** `sriov-operator/SriovNetworkNodePolicy.yaml`
- **Note:** https://docs.openshift.com/container-platform/4.20/scalability_and_performance/telco_ref_design_specs/ran/telco-ran-ref-du-components.html#telco-ran-sr-iov-operator_ran-ref-design-components

```diff
diff -u -N /tmp/MERGED-1698890527/sriovnetwork-openshift-io-v1_sriovnetworknodepolicy_openshift-sriov-network-operator_policy-fh3 /tmp/LIVE-492428565/sriovnetwork-openshift-io-v1_sriovnetworknodepolicy_openshift-sriov-network-operator_policy-fh3
--- /tmp/MERGED-1698890527/sriovnetwork-openshift-io-v1_sriovnetworknodepolicy_openshift-sriov-network-operator_policy-fh3	2026-04-28 10:47:32.180441159 -0400
+++ /tmp/LIVE-492428565/sriovnetwork-openshift-io-v1_sriovnetworknodepolicy_openshift-sriov-network-operator_policy-fh3	2026-04-28 10:47:32.180441159 -0400
@@ -12,7 +12,7 @@
     - ens1f3#4-7
     vendor: "8086"
   nodeSelector:
-    node-role.kubernetes.io/.*: Prefix must match
+    feature.node.kubernetes.io/network-sriov.capable: "true"
   numVfs: 8
   priority: 99
   resourceName: pci_sriov_net_fh3
```

### sriovnetwork.openshift.io/v1_SriovNetworkNodePolicy_openshift-sriov-network-operator_policy-fh3m

- **Template:** `sriov-operator/SriovNetworkNodePolicy.yaml`
- **Note:** https://docs.openshift.com/container-platform/4.20/scalability_and_performance/telco_ref_design_specs/ran/telco-ran-ref-du-components.html#telco-ran-sr-iov-operator_ran-ref-design-components

```diff
diff -u -N /tmp/MERGED-3888981775/sriovnetwork-openshift-io-v1_sriovnetworknodepolicy_openshift-sriov-network-operator_policy-fh3m /tmp/LIVE-3728153024/sriovnetwork-openshift-io-v1_sriovnetworknodepolicy_openshift-sriov-network-operator_policy-fh3m
--- /tmp/MERGED-3888981775/sriovnetwork-openshift-io-v1_sriovnetworknodepolicy_openshift-sriov-network-operator_policy-fh3m	2026-04-28 10:47:32.182441149 -0400
+++ /tmp/LIVE-3728153024/sriovnetwork-openshift-io-v1_sriovnetworknodepolicy_openshift-sriov-network-operator_policy-fh3m	2026-04-28 10:47:32.182441149 -0400
@@ -12,7 +12,7 @@
     - ens1f3#0-3
     vendor: "8086"
   nodeSelector:
-    node-role.kubernetes.io/.*: Prefix must match
+    feature.node.kubernetes.io/network-sriov.capable: "true"
   numVfs: 8
   priority: 99
   resourceName: pci_sriov_net_fh3m
```

### sriovnetwork.openshift.io/v1_SriovNetworkNodePolicy_openshift-sriov-network-operator_policy-fh4

- **Template:** `sriov-operator/SriovNetworkNodePolicy.yaml`
- **Note:** https://docs.openshift.com/container-platform/4.20/scalability_and_performance/telco_ref_design_specs/ran/telco-ran-ref-du-components.html#telco-ran-sr-iov-operator_ran-ref-design-components

```diff
diff -u -N /tmp/MERGED-1352774303/sriovnetwork-openshift-io-v1_sriovnetworknodepolicy_openshift-sriov-network-operator_policy-fh4 /tmp/LIVE-1211764233/sriovnetwork-openshift-io-v1_sriovnetworknodepolicy_openshift-sriov-network-operator_policy-fh4
--- /tmp/MERGED-1352774303/sriovnetwork-openshift-io-v1_sriovnetworknodepolicy_openshift-sriov-network-operator_policy-fh4	2026-04-28 10:47:32.184441138 -0400
+++ /tmp/LIVE-1211764233/sriovnetwork-openshift-io-v1_sriovnetworknodepolicy_openshift-sriov-network-operator_policy-fh4	2026-04-28 10:47:32.184441138 -0400
@@ -12,7 +12,7 @@
     - ens2f0#4-7
     vendor: "8086"
   nodeSelector:
-    node-role.kubernetes.io/.*: Prefix must match
+    feature.node.kubernetes.io/network-sriov.capable: "true"
   numVfs: 8
   priority: 99
   resourceName: pci_sriov_net_fh4
```

### sriovnetwork.openshift.io/v1_SriovNetworkNodePolicy_openshift-sriov-network-operator_policy-fh4m

- **Template:** `sriov-operator/SriovNetworkNodePolicy.yaml`
- **Note:** https://docs.openshift.com/container-platform/4.20/scalability_and_performance/telco_ref_design_specs/ran/telco-ran-ref-du-components.html#telco-ran-sr-iov-operator_ran-ref-design-components

```diff
diff -u -N /tmp/MERGED-2380249111/sriovnetwork-openshift-io-v1_sriovnetworknodepolicy_openshift-sriov-network-operator_policy-fh4m /tmp/LIVE-2139990499/sriovnetwork-openshift-io-v1_sriovnetworknodepolicy_openshift-sriov-network-operator_policy-fh4m
--- /tmp/MERGED-2380249111/sriovnetwork-openshift-io-v1_sriovnetworknodepolicy_openshift-sriov-network-operator_policy-fh4m	2026-04-28 10:47:32.186441127 -0400
+++ /tmp/LIVE-2139990499/sriovnetwork-openshift-io-v1_sriovnetworknodepolicy_openshift-sriov-network-operator_policy-fh4m	2026-04-28 10:47:32.186441127 -0400
@@ -12,7 +12,7 @@
     - ens2f0#0-3
     vendor: "8086"
   nodeSelector:
-    node-role.kubernetes.io/.*: Prefix must match
+    feature.node.kubernetes.io/network-sriov.capable: "true"
   numVfs: 8
   priority: 99
   resourceName: pci_sriov_net_fh4m
```

### sriovnetwork.openshift.io/v1_SriovNetworkNodePolicy_openshift-sriov-network-operator_policy-fh5

- **Template:** `sriov-operator/SriovNetworkNodePolicy.yaml`
- **Note:** https://docs.openshift.com/container-platform/4.20/scalability_and_performance/telco_ref_design_specs/ran/telco-ran-ref-du-components.html#telco-ran-sr-iov-operator_ran-ref-design-components

```diff
diff -u -N /tmp/MERGED-1189108314/sriovnetwork-openshift-io-v1_sriovnetworknodepolicy_openshift-sriov-network-operator_policy-fh5 /tmp/LIVE-3360210255/sriovnetwork-openshift-io-v1_sriovnetworknodepolicy_openshift-sriov-network-operator_policy-fh5
--- /tmp/MERGED-1189108314/sriovnetwork-openshift-io-v1_sriovnetworknodepolicy_openshift-sriov-network-operator_policy-fh5	2026-04-28 10:47:32.189441111 -0400
+++ /tmp/LIVE-3360210255/sriovnetwork-openshift-io-v1_sriovnetworknodepolicy_openshift-sriov-network-operator_policy-fh5	2026-04-28 10:47:32.189441111 -0400
@@ -12,7 +12,7 @@
     - ens2f1#4-7
     vendor: "8086"
   nodeSelector:
-    node-role.kubernetes.io/.*: Prefix must match
+    feature.node.kubernetes.io/network-sriov.capable: "true"
   numVfs: 8
   priority: 99
   resourceName: pci_sriov_net_fh5
```

### sriovnetwork.openshift.io/v1_SriovNetworkNodePolicy_openshift-sriov-network-operator_policy-fh5m

- **Template:** `sriov-operator/SriovNetworkNodePolicy.yaml`
- **Note:** https://docs.openshift.com/container-platform/4.20/scalability_and_performance/telco_ref_design_specs/ran/telco-ran-ref-du-components.html#telco-ran-sr-iov-operator_ran-ref-design-components

```diff
diff -u -N /tmp/MERGED-495332412/sriovnetwork-openshift-io-v1_sriovnetworknodepolicy_openshift-sriov-network-operator_policy-fh5m /tmp/LIVE-2340893980/sriovnetwork-openshift-io-v1_sriovnetworknodepolicy_openshift-sriov-network-operator_policy-fh5m
--- /tmp/MERGED-495332412/sriovnetwork-openshift-io-v1_sriovnetworknodepolicy_openshift-sriov-network-operator_policy-fh5m	2026-04-28 10:47:32.191441100 -0400
+++ /tmp/LIVE-2340893980/sriovnetwork-openshift-io-v1_sriovnetworknodepolicy_openshift-sriov-network-operator_policy-fh5m	2026-04-28 10:47:32.191441100 -0400
@@ -12,7 +12,7 @@
     - ens2f1#0-3
     vendor: "8086"
   nodeSelector:
-    node-role.kubernetes.io/.*: Prefix must match
+    feature.node.kubernetes.io/network-sriov.capable: "true"
   numVfs: 8
   priority: 99
   resourceName: pci_sriov_net_fh5m
```

### sriovnetwork.openshift.io/v1_SriovNetworkNodePolicy_openshift-sriov-network-operator_policy-fh6

- **Template:** `sriov-operator/SriovNetworkNodePolicy.yaml`
- **Note:** https://docs.openshift.com/container-platform/4.20/scalability_and_performance/telco_ref_design_specs/ran/telco-ran-ref-du-components.html#telco-ran-sr-iov-operator_ran-ref-design-components

```diff
diff -u -N /tmp/MERGED-2359840463/sriovnetwork-openshift-io-v1_sriovnetworknodepolicy_openshift-sriov-network-operator_policy-fh6 /tmp/LIVE-2589982196/sriovnetwork-openshift-io-v1_sriovnetworknodepolicy_openshift-sriov-network-operator_policy-fh6
--- /tmp/MERGED-2359840463/sriovnetwork-openshift-io-v1_sriovnetworknodepolicy_openshift-sriov-network-operator_policy-fh6	2026-04-28 10:47:32.194441084 -0400
+++ /tmp/LIVE-2589982196/sriovnetwork-openshift-io-v1_sriovnetworknodepolicy_openshift-sriov-network-operator_policy-fh6	2026-04-28 10:47:32.194441084 -0400
@@ -12,7 +12,7 @@
     - ens2f2#4-7
     vendor: "8086"
   nodeSelector:
-    node-role.kubernetes.io/.*: Prefix must match
+    feature.node.kubernetes.io/network-sriov.capable: "true"
   numVfs: 8
   priority: 99
   resourceName: pci_sriov_net_fh6
```

### sriovnetwork.openshift.io/v1_SriovNetworkNodePolicy_openshift-sriov-network-operator_policy-fh6m

- **Template:** `sriov-operator/SriovNetworkNodePolicy.yaml`
- **Note:** https://docs.openshift.com/container-platform/4.20/scalability_and_performance/telco_ref_design_specs/ran/telco-ran-ref-du-components.html#telco-ran-sr-iov-operator_ran-ref-design-components

```diff
diff -u -N /tmp/MERGED-1994534548/sriovnetwork-openshift-io-v1_sriovnetworknodepolicy_openshift-sriov-network-operator_policy-fh6m /tmp/LIVE-266280391/sriovnetwork-openshift-io-v1_sriovnetworknodepolicy_openshift-sriov-network-operator_policy-fh6m
--- /tmp/MERGED-1994534548/sriovnetwork-openshift-io-v1_sriovnetworknodepolicy_openshift-sriov-network-operator_policy-fh6m	2026-04-28 10:47:32.196441073 -0400
+++ /tmp/LIVE-266280391/sriovnetwork-openshift-io-v1_sriovnetworknodepolicy_openshift-sriov-network-operator_policy-fh6m	2026-04-28 10:47:32.196441073 -0400
@@ -12,7 +12,7 @@
     - ens2f2#0-3
     vendor: "8086"
   nodeSelector:
-    node-role.kubernetes.io/.*: Prefix must match
+    feature.node.kubernetes.io/network-sriov.capable: "true"
   numVfs: 8
   priority: 99
   resourceName: pci_sriov_net_fh6m
```

### sriovnetwork.openshift.io/v1_SriovNetworkNodePolicy_openshift-sriov-network-operator_policy-fh7

- **Template:** `sriov-operator/SriovNetworkNodePolicy.yaml`
- **Note:** https://docs.openshift.com/container-platform/4.20/scalability_and_performance/telco_ref_design_specs/ran/telco-ran-ref-du-components.html#telco-ran-sr-iov-operator_ran-ref-design-components

```diff
diff -u -N /tmp/MERGED-2348970542/sriovnetwork-openshift-io-v1_sriovnetworknodepolicy_openshift-sriov-network-operator_policy-fh7 /tmp/LIVE-3790187363/sriovnetwork-openshift-io-v1_sriovnetworknodepolicy_openshift-sriov-network-operator_policy-fh7
--- /tmp/MERGED-2348970542/sriovnetwork-openshift-io-v1_sriovnetworknodepolicy_openshift-sriov-network-operator_policy-fh7	2026-04-28 10:47:32.199441057 -0400
+++ /tmp/LIVE-3790187363/sriovnetwork-openshift-io-v1_sriovnetworknodepolicy_openshift-sriov-network-operator_policy-fh7	2026-04-28 10:47:32.199441057 -0400
@@ -12,7 +12,7 @@
     - ens2f3#4-7
     vendor: "8086"
   nodeSelector:
-    node-role.kubernetes.io/.*: Prefix must match
+    feature.node.kubernetes.io/network-sriov.capable: "true"
   numVfs: 8
   priority: 99
   resourceName: pci_sriov_net_fh7
```

### sriovnetwork.openshift.io/v1_SriovNetworkNodePolicy_openshift-sriov-network-operator_policy-fh7m

- **Template:** `sriov-operator/SriovNetworkNodePolicy.yaml`
- **Note:** https://docs.openshift.com/container-platform/4.20/scalability_and_performance/telco_ref_design_specs/ran/telco-ran-ref-du-components.html#telco-ran-sr-iov-operator_ran-ref-design-components

```diff
diff -u -N /tmp/MERGED-1022464844/sriovnetwork-openshift-io-v1_sriovnetworknodepolicy_openshift-sriov-network-operator_policy-fh7m /tmp/LIVE-3598533268/sriovnetwork-openshift-io-v1_sriovnetworknodepolicy_openshift-sriov-network-operator_policy-fh7m
--- /tmp/MERGED-1022464844/sriovnetwork-openshift-io-v1_sriovnetworknodepolicy_openshift-sriov-network-operator_policy-fh7m	2026-04-28 10:47:32.202441040 -0400
+++ /tmp/LIVE-3598533268/sriovnetwork-openshift-io-v1_sriovnetworknodepolicy_openshift-sriov-network-operator_policy-fh7m	2026-04-28 10:47:32.202441040 -0400
@@ -12,7 +12,7 @@
     - ens2f3#0-3
     vendor: "8086"
   nodeSelector:
-    node-role.kubernetes.io/.*: Prefix must match
+    feature.node.kubernetes.io/network-sriov.capable: "true"
   numVfs: 8
   priority: 99
   resourceName: pci_sriov_net_fh7m
```

### sriovnetwork.openshift.io/v1_SriovNetworkNodePolicy_openshift-sriov-network-operator_policy-fh8

- **Template:** `sriov-operator/SriovNetworkNodePolicy.yaml`
- **Note:** https://docs.openshift.com/container-platform/4.20/scalability_and_performance/telco_ref_design_specs/ran/telco-ran-ref-du-components.html#telco-ran-sr-iov-operator_ran-ref-design-components

```diff
diff -u -N /tmp/MERGED-182342112/sriovnetwork-openshift-io-v1_sriovnetworknodepolicy_openshift-sriov-network-operator_policy-fh8 /tmp/LIVE-2273029096/sriovnetwork-openshift-io-v1_sriovnetworknodepolicy_openshift-sriov-network-operator_policy-fh8
--- /tmp/MERGED-182342112/sriovnetwork-openshift-io-v1_sriovnetworknodepolicy_openshift-sriov-network-operator_policy-fh8	2026-04-28 10:47:32.204441029 -0400
+++ /tmp/LIVE-2273029096/sriovnetwork-openshift-io-v1_sriovnetworknodepolicy_openshift-sriov-network-operator_policy-fh8	2026-04-28 10:47:32.204441029 -0400
@@ -12,7 +12,7 @@
     - ens3f0#4-7
     vendor: "8086"
   nodeSelector:
-    node-role.kubernetes.io/.*: Prefix must match
+    feature.node.kubernetes.io/network-sriov.capable: "true"
   numVfs: 8
   priority: 99
   resourceName: pci_sriov_net_fh8
```

### sriovnetwork.openshift.io/v1_SriovNetworkNodePolicy_openshift-sriov-network-operator_policy-fh8m

- **Template:** `sriov-operator/SriovNetworkNodePolicy.yaml`
- **Note:** https://docs.openshift.com/container-platform/4.20/scalability_and_performance/telco_ref_design_specs/ran/telco-ran-ref-du-components.html#telco-ran-sr-iov-operator_ran-ref-design-components

```diff
diff -u -N /tmp/MERGED-1999268446/sriovnetwork-openshift-io-v1_sriovnetworknodepolicy_openshift-sriov-network-operator_policy-fh8m /tmp/LIVE-357171191/sriovnetwork-openshift-io-v1_sriovnetworknodepolicy_openshift-sriov-network-operator_policy-fh8m
--- /tmp/MERGED-1999268446/sriovnetwork-openshift-io-v1_sriovnetworknodepolicy_openshift-sriov-network-operator_policy-fh8m	2026-04-28 10:47:32.207441013 -0400
+++ /tmp/LIVE-357171191/sriovnetwork-openshift-io-v1_sriovnetworknodepolicy_openshift-sriov-network-operator_policy-fh8m	2026-04-28 10:47:32.207441013 -0400
@@ -12,7 +12,7 @@
     - ens3f0#0-3
     vendor: "8086"
   nodeSelector:
-    node-role.kubernetes.io/.*: Prefix must match
+    feature.node.kubernetes.io/network-sriov.capable: "true"
   numVfs: 8
   priority: 99
   resourceName: pci_sriov_net_fh8m
```

### sriovnetwork.openshift.io/v1_SriovNetworkNodePolicy_openshift-sriov-network-operator_policy-fh9

- **Template:** `sriov-operator/SriovNetworkNodePolicy.yaml`
- **Note:** https://docs.openshift.com/container-platform/4.20/scalability_and_performance/telco_ref_design_specs/ran/telco-ran-ref-du-components.html#telco-ran-sr-iov-operator_ran-ref-design-components

```diff
diff -u -N /tmp/MERGED-2731812875/sriovnetwork-openshift-io-v1_sriovnetworknodepolicy_openshift-sriov-network-operator_policy-fh9 /tmp/LIVE-3904382962/sriovnetwork-openshift-io-v1_sriovnetworknodepolicy_openshift-sriov-network-operator_policy-fh9
--- /tmp/MERGED-2731812875/sriovnetwork-openshift-io-v1_sriovnetworknodepolicy_openshift-sriov-network-operator_policy-fh9	2026-04-28 10:47:32.209441003 -0400
+++ /tmp/LIVE-3904382962/sriovnetwork-openshift-io-v1_sriovnetworknodepolicy_openshift-sriov-network-operator_policy-fh9	2026-04-28 10:47:32.209441003 -0400
@@ -12,7 +12,7 @@
     - ens3f1#4-7
     vendor: "8086"
   nodeSelector:
-    node-role.kubernetes.io/.*: Prefix must match
+    feature.node.kubernetes.io/network-sriov.capable: "true"
   numVfs: 8
   priority: 99
   resourceName: pci_sriov_net_fh9
```

### sriovnetwork.openshift.io/v1_SriovNetworkNodePolicy_openshift-sriov-network-operator_policy-fh9m

- **Template:** `sriov-operator/SriovNetworkNodePolicy.yaml`
- **Note:** https://docs.openshift.com/container-platform/4.20/scalability_and_performance/telco_ref_design_specs/ran/telco-ran-ref-du-components.html#telco-ran-sr-iov-operator_ran-ref-design-components

```diff
diff -u -N /tmp/MERGED-3872329276/sriovnetwork-openshift-io-v1_sriovnetworknodepolicy_openshift-sriov-network-operator_policy-fh9m /tmp/LIVE-1548385898/sriovnetwork-openshift-io-v1_sriovnetworknodepolicy_openshift-sriov-network-operator_policy-fh9m
--- /tmp/MERGED-3872329276/sriovnetwork-openshift-io-v1_sriovnetworknodepolicy_openshift-sriov-network-operator_policy-fh9m	2026-04-28 10:47:32.211440992 -0400
+++ /tmp/LIVE-1548385898/sriovnetwork-openshift-io-v1_sriovnetworknodepolicy_openshift-sriov-network-operator_policy-fh9m	2026-04-28 10:47:32.212440986 -0400
@@ -12,7 +12,7 @@
     - ens3f1#0-3
     vendor: "8086"
   nodeSelector:
-    node-role.kubernetes.io/.*: Prefix must match
+    feature.node.kubernetes.io/network-sriov.capable: "true"
   numVfs: 8
   priority: 99
   resourceName: pci_sriov_net_fh9m
```

### sriovnetwork.openshift.io/v1_SriovOperatorConfig_openshift-sriov-network-operator_default

- **Template:** `sriov-operator/SriovOperatorConfigForSNO.yaml`
- **Note:** https://docs.openshift.com/container-platform/4.20/scalability_and_performance/telco_ref_design_specs/ran/telco-ran-ref-du-components.html#telco-ran-sr-iov-operator_ran-ref-design-components

```diff
diff -u -N /tmp/MERGED-3283911739/sriovnetwork-openshift-io-v1_sriovoperatorconfig_openshift-sriov-network-operator_default /tmp/LIVE-2307322030/sriovnetwork-openshift-io-v1_sriovoperatorconfig_openshift-sriov-network-operator_default
--- /tmp/MERGED-3283911739/sriovnetwork-openshift-io-v1_sriovoperatorconfig_openshift-sriov-network-operator_default	2026-04-28 10:47:32.273440656 -0400
+++ /tmp/LIVE-2307322030/sriovnetwork-openshift-io-v1_sriovoperatorconfig_openshift-sriov-network-operator_default	2026-04-28 10:47:32.273440656 -0400
@@ -6,7 +6,7 @@
 spec:
   configDaemonNodeSelector:
     node-role.kubernetes.io/worker: ""
-  disableDrain: true
-  enableInjector: false
-  enableOperatorWebhook: false
-  logLevel: 0
+  disableDrain: false
+  enableInjector: true
+  enableOperatorWebhook: true
+  logLevel: 2
```

### operators.coreos.com/v1alpha1_Subscription_openshift-storage_lvms-operator

- **Template:** `storage-lvm/StorageLVMSubscription.yaml`
- **Note:** https://docs.openshift.com/container-platform/4.20/scalability_and_performance/telco_ref_design_specs/ran/telco-ran-ref-du-components.html#telco-ran-lvms-operator_ran-ref-design-components

```diff
diff -u -N /tmp/MERGED-1493462026/operators-coreos-com-v1alpha1_subscription_openshift-storage_lvms-operator /tmp/LIVE-1400053612/operators-coreos-com-v1alpha1_subscription_openshift-storage_lvms-operator
--- /tmp/MERGED-1493462026/operators-coreos-com-v1alpha1_subscription_openshift-storage_lvms-operator	2026-04-28 10:47:32.277440635 -0400
+++ /tmp/LIVE-1400053612/operators-coreos-com-v1alpha1_subscription_openshift-storage_lvms-operator	2026-04-28 10:47:32.277440635 -0400
@@ -6,7 +6,6 @@
   name: lvms-operator
   namespace: openshift-storage
 spec:
-  channel: stable
   installPlanApproval: Manual
   name: lvms-operator
   source: cs-redhat-operator-index
```


---
*Automated summary: 36 resources listed with non-empty diff output.*
