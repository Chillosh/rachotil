"""
Module for managing the UFW firewall on the remote server.
"""

from ...components.ssh.ssh import SSH

class FirewallManager:
    """
    Manager class for UFW firewall operations including rule management and status toggling.
    """

    def __init__(self, ssh_client: SSH):
        """
        Initialize the FirewallManager.

        Args:
            ssh_client (SSH): Connected SSH client instance.
        """
        self.ssh = ssh_client

    def toggle_ufw(self, action: str) -> tuple[bool, str]:
        """
        Enable or disable the UFW firewall.

        Args:
            action (str): Either "enable" or "disable".

        Returns:
            tuple[bool, str]: A success flag and the output message.
        """
        if not self.ssh:
            return False, "SSH client is not connected."
        
        if action not in ["enable", "disable"]:
            return False, "Invalid action."
            
        out, err = self.ssh.run_sudo_command(f"ufw --force {action}")
        return True, out.strip() or err.strip()

    def get_status_and_rules(self) -> tuple[bool, str, list[tuple[str, str, str, str]]]:
        """
        Fetch the current status of UFW and parse active rules.

        Returns:
            tuple[bool, str, list[tuple[str, str, str, str]]]: A success flag, status message, and a list of parsed rules.
        """
        if not self.ssh:
            return False, "SSH client is not connected.", []
            
        out, err = self.ssh.run_sudo_command("ufw status numbered")
        
        if "inactive" in out.lower():
            return True, "UFW is currently INACTIVE.", []
            
        lines = out.split("\n")
        results = []
        parsing_rules = False
        
        for line in lines:
            if line.startswith("[ 1]"): 
                parsing_rules = True
            
            if parsing_rules and line.strip() and line.startswith("["):
                parts = line.replace("]", "").replace("[", "").split()
                if len(parts) >= 4:
                    rule_id = parts[0].strip()
                    rule_to = parts[1].strip()
                    rule_action = parts[2].strip()
                    rule_from = parts[3].strip()
                    results.append((rule_id, rule_to, rule_action, rule_from))
                    
        return True, "UFW is ACTIVE. Rules loaded.", results

    def add_rule(self, port: str, proto: str) -> tuple[bool, str]:
        """
        Add a new allowance rule to the firewall.

        Args:
            port (str): The port or service name.
            proto (str): The protocol ("tcp", "udp", or None).

        Returns:
            tuple[bool, str]: A success flag and the output message.
        """
        if not self.ssh:
            return False, "SSH client is not connected."
            
        if not port:
            return False, "Port is required."
            
        cmd = f"ufw allow {port}"
        if proto in ["tcp", "udp"]:
            cmd += f"/{proto}"
            
        out, err = self.ssh.run_sudo_command(cmd)
        return True, out.strip() or err.strip()

    def delete_rule(self, rule_id: str) -> tuple[bool, str]:
        """
        Delete a firewall rule by its numerical ID.

        Args:
            rule_id (str): The ID of the rule to delete.

        Returns:
            tuple[bool, str]: A success flag and the output message.
        """
        if not self.ssh:
            return False, "SSH client is not connected."
            
        out, err = self.ssh.run_sudo_command(f"ufw --force delete {rule_id}")
        return True, out.strip() or err.strip()