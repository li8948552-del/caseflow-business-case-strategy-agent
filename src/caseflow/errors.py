class CaseFlowError(Exception):
    """Base domain error."""


class InvalidTransitionError(CaseFlowError):
    pass


class PolicyViolationError(CaseFlowError):
    pass


class CaseBusyError(CaseFlowError):
    pass
