"""
Access Control Module for SOC 2 Compliance

This module provides access control and authorization capabilities:
- File access validation
- Role-based access control (RBAC)
- Permission checking
- Access logging
"""

import os
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set

from pydantic import BaseModel


class AccessLevel(str, Enum):
    """Access levels for resources"""
    NONE = "none"
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"


class Role(str, Enum):
    """User roles"""
    VIEWER = "viewer"  # Can read logs and view reports
    ANALYST = "analyst"  # Can analyze logs and generate reports
    ADMIN = "admin"  # Can modify configurations and access all data
    AUDITOR = "auditor"  # Can view audit logs and compliance reports


class Permission(BaseModel):
    """Permission model"""
    resource_type: str
    access_level: AccessLevel
    conditions: Dict[str, any] = {}


class AccessPolicy(BaseModel):
    """Access policy for a role"""
    role: Role
    permissions: List[Permission]
    description: str


class AccessControl:
    """
    Access control service for SOC 2 compliance.

    Features:
    - Role-based access control
    - File access validation
    - Permission checking
    - Access logging integration
    """

    # Default access policies
    DEFAULT_POLICIES: Dict[Role, List[Permission]] = {
        Role.VIEWER: [
            Permission(resource_type="logs", access_level=AccessLevel.READ),
            Permission(resource_type="reports", access_level=AccessLevel.READ),
        ],
        Role.ANALYST: [
            Permission(resource_type="logs", access_level=AccessLevel.READ),
            Permission(resource_type="reports", access_level=AccessLevel.WRITE),
            Permission(resource_type="analysis", access_level=AccessLevel.WRITE),
        ],
        Role.ADMIN: [
            Permission(resource_type="logs", access_level=AccessLevel.ADMIN),
            Permission(resource_type="reports", access_level=AccessLevel.ADMIN),
            Permission(resource_type="config", access_level=AccessLevel.ADMIN),
            Permission(resource_type="analysis", access_level=AccessLevel.ADMIN),
        ],
        Role.AUDITOR: [
            Permission(resource_type="audit_logs", access_level=AccessLevel.READ),
            Permission(resource_type="compliance_reports", access_level=AccessLevel.READ),
            Permission(resource_type="logs", access_level=AccessLevel.READ),
        ],
    }

    def __init__(self, default_role: Role = Role.ANALYST):
        """
        Initialize access control

        Args:
            default_role: Default role for current user
        """
        self.default_role = default_role
        self.user_roles: Dict[str, Role] = {}

        # Load user from environment
        current_user = os.getenv('USER', 'unknown')
        self.current_user = current_user
        self.user_roles[current_user] = default_role

    def get_user_role(self, user: Optional[str] = None) -> Role:
        """
        Get role for a user

        Args:
            user: Username (defaults to current user)

        Returns:
            User's role
        """
        user = user or self.current_user
        return self.user_roles.get(user, self.default_role)

    def set_user_role(self, user: str, role: Role):
        """
        Set role for a user

        Args:
            user: Username
            role: Role to assign
        """
        self.user_roles[user] = role

    def check_permission(
        self,
        resource_type: str,
        access_level: AccessLevel,
        user: Optional[str] = None,
    ) -> bool:
        """
        Check if user has required permission

        Args:
            resource_type: Type of resource being accessed
            access_level: Required access level
            user: Username (defaults to current user)

        Returns:
            True if user has permission, False otherwise
        """
        role = self.get_user_role(user)
        permissions = self.DEFAULT_POLICIES.get(role, [])

        for perm in permissions:
            if perm.resource_type == resource_type:
                # Check if user's access level meets requirement
                levels = [AccessLevel.NONE, AccessLevel.READ, AccessLevel.WRITE, AccessLevel.ADMIN]
                user_level_idx = levels.index(perm.access_level)
                required_level_idx = levels.index(access_level)

                if user_level_idx >= required_level_idx:
                    return True

        return False

    def validate_file_access(
        self,
        file_path: str,
        operation: str = "read",
        user: Optional[str] = None,
    ) -> bool:
        """
        Validate file access permission

        Args:
            file_path: Path to file
            operation: Operation type (read/write)
            user: Username (defaults to current user)

        Returns:
            True if access is allowed, False otherwise
        """
        path = Path(file_path)

        # Determine resource type based on file path
        if "audit" in str(path):
            resource_type = "audit_logs"
        elif "config" in str(path):
            resource_type = "config"
        elif "compliance" in str(path):
            resource_type = "compliance_reports"
        elif any(ext in path.suffixes for ext in ['.log', '.txt']):
            resource_type = "logs"
        else:
            resource_type = "reports"

        # Map operation to access level
        access_level = AccessLevel.READ if operation == "read" else AccessLevel.WRITE

        return self.check_permission(resource_type, access_level, user)

    def check_file_permissions(self, file_path: str) -> Dict[str, bool]:
        """
        Check OS-level file permissions

        Args:
            file_path: Path to file

        Returns:
            Dictionary with read/write/execute permissions
        """
        path = Path(file_path)

        if not path.exists():
            return {"exists": False, "read": False, "write": False, "execute": False}

        return {
            "exists": True,
            "read": os.access(path, os.R_OK),
            "write": os.access(path, os.W_OK),
            "execute": os.access(path, os.X_OK),
        }

    def enforce_file_permissions(self, file_path: str, mode: int = 0o600):
        """
        Enforce restrictive file permissions

        Args:
            file_path: Path to file
            mode: Permission mode (default: owner read/write only)
        """
        path = Path(file_path)
        if path.exists():
            os.chmod(path, mode)

    def get_user_permissions(self, user: Optional[str] = None) -> List[Permission]:
        """
        Get all permissions for a user

        Args:
            user: Username (defaults to current user)

        Returns:
            List of permissions
        """
        role = self.get_user_role(user)
        return self.DEFAULT_POLICIES.get(role, [])

    def get_accessible_resources(
        self,
        resource_type: str,
        user: Optional[str] = None,
    ) -> AccessLevel:
        """
        Get access level for a resource type

        Args:
            resource_type: Type of resource
            user: Username (defaults to current user)

        Returns:
            Highest access level available
        """
        permissions = self.get_user_permissions(user)

        highest_level = AccessLevel.NONE
        levels = [AccessLevel.NONE, AccessLevel.READ, AccessLevel.WRITE, AccessLevel.ADMIN]

        for perm in permissions:
            if perm.resource_type == resource_type:
                current_idx = levels.index(perm.access_level)
                highest_idx = levels.index(highest_level)

                if current_idx > highest_idx:
                    highest_level = perm.access_level

        return highest_level

    def generate_access_report(self) -> Dict[str, any]:
        """
        Generate access control report for compliance

        Returns:
            Dictionary containing access control information
        """
        return {
            "current_user": self.current_user,
            "current_role": self.get_user_role().value,
            "all_users": {
                user: role.value
                for user, role in self.user_roles.items()
            },
            "role_definitions": {
                role.value: [
                    {
                        "resource_type": perm.resource_type,
                        "access_level": perm.access_level.value,
                    }
                    for perm in perms
                ]
                for role, perms in self.DEFAULT_POLICIES.items()
            },
            "current_user_permissions": [
                {
                    "resource_type": perm.resource_type,
                    "access_level": perm.access_level.value,
                }
                for perm in self.get_user_permissions()
            ],
        }


# Global access control instance
_global_access_control: Optional[AccessControl] = None


def get_access_control() -> AccessControl:
    """Get or create the global access control instance"""
    global _global_access_control
    if _global_access_control is None:
        _global_access_control = AccessControl()
    return _global_access_control
