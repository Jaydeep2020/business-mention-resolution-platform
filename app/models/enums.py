from enum import Enum

class UserRole(str, Enum):
    ADMIN = 'admin'
    REVIEWER = 'reviewer'
    VIEWER = 'viewer'

class ResolutionStatus(str, Enum):
    PENDING = 'pending'
    AUTO_RESOLVED = 'auto_resolved'
    SENT_FOR_REVIEWER = 'sent_for_reviewer'
    APPROVED = 'approved'
    REJECTED = 'rejected'

class ResolutionDecision(str, Enum):
    AUTO = 'auto'
    REVIEW = 'review'
    APPROVED = 'approved'
    REJECTED = 'rejected'

class SourceType(str, Enum):
    REVIEW = 'review'