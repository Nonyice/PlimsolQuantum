class RiskGuardian:
    """
    Final authority before any trade is executed.
    """

    async def approve(self, trading_account, decision):

        if decision.action == "WAIT":
            return False

        return True