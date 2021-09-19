from scripts.helpful_scripts import LOCAL_BLOCKCHAIN_ENVIRONMENTS, get_account, fund_with_link
from scripts.deploy_lottery import deploy_lottery
from brownie import network
import pytest
import time

def test_can_pick_winner():
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    lottery = deploy_lottery()
    account0 = get_account(index=0)
    account1 = get_account(index=1)
    account2 = get_account(index=2)
    lottery.startLottery({'from': account1})
    lottery.enter({'from': account0, 'value': lottery.getEntranceFee()+1})
    lottery.enter({'from': account1, 'value': lottery.getEntranceFee()+1})
    lottery.enter({'from': account2, 'value': lottery.getEntranceFee()+1})
    fund_with_link(lottery)
    lottery.endLottery({'from': account1})
    time.sleep(60)
    assert lottery.recentWinner() == account1 or lottery.recentWinner == account2 or lottery.recentWinner() == account2
    assert lottery.balance() == 0