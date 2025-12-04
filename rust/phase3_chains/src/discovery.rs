use anyhow::{Context, Result};
use log::{info, warn};
use mdns_sd::{ServiceDaemon, ServiceInfo};
use std::net::IpAddr;
use std::time::Duration;

const SERVICE_TYPE: &str = "_phase3._tcp.local.";

/// Announce the coordinator service via mDNS
pub fn announce_coordinator(port: u16) -> Result<ServiceDaemon> {
    let mdns = ServiceDaemon::new().context("Failed to create mDNS daemon")?;
    
    let hostname = gethostname::gethostname();
    let hostname_str = hostname.to_string_lossy();
    let instance_name = format!("phase3-coordinator-{}", hostname_str);
    
    let service_info = ServiceInfo::new(
        SERVICE_TYPE,
        &instance_name,
        &hostname_str,
        (),
        port,
        None,
    )
    .context("Failed to create service info")?
    .enable_addr_auto();
    
    mdns.register(service_info)
        .context("Failed to register mDNS service")?;
    
    info!("🔊 Announcing coordinator on mDNS as '{}'", instance_name);
    
    Ok(mdns)
}

/// Discover a coordinator via mDNS
pub fn discover_coordinator(timeout: Duration) -> Result<String> {
    info!("🔍 Discovering coordinator via mDNS...");
    
    let mdns = ServiceDaemon::new().context("Failed to create mDNS daemon")?;
    let receiver = mdns.browse(SERVICE_TYPE).context("Failed to browse services")?;
    
    let start = std::time::Instant::now();
    
    while start.elapsed() < timeout {
        if let Ok(event) = receiver.recv_timeout(Duration::from_secs(1)) {
            match event {
                mdns_sd::ServiceEvent::ServiceResolved(info) => {
                    // Get the first IPv4 address
                    if let Some(addr) = info.get_addresses().iter().find_map(|addr| {
                        if let IpAddr::V4(ipv4) = addr {
                            Some(ipv4)
                        } else {
                            None
                        }
                    }) {
                        let coordinator_addr = format!("{}:{}", addr, info.get_port());
                        info!("✓ Found coordinator at {}", coordinator_addr);
                        return Ok(coordinator_addr);
                    }
                }
                mdns_sd::ServiceEvent::SearchStarted(_) => {
                    info!("  mDNS search started...");
                }
                _ => {}
            }
        }
    }
    
    warn!("No coordinator found within timeout");
    anyhow::bail!("Coordinator discovery timeout")
}
