from aiogram.fsm.state import State, StatesGroup


class DepositStates(StatesGroup):
    """Состояния для процесса пополнения"""
    waiting_for_amount = State()
    waiting_for_description = State()
    confirming_deposit = State()


class WithdrawStates(StatesGroup):
    """Состояния для процесса вывода средств"""
    waiting_for_amount = State()
    waiting_for_payment_method = State()
    waiting_for_payment_details = State()
    confirming_withdraw = State()
