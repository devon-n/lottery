from brownie import Lottery, accounts, network, config, exceptions
from scripts.deploy_lottery import deploy_lottery
from scripts.helpful_scripts import LOCAL_BLOCKCHAIN_ENVIRONMENTS, get_account, fund_with_link, get_contract
from web3 import Web3
import pytest


def test_get_entrance_fee():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    # Arrange
    lottery = deploy_lottery()
    # Act
    entrance_fee = lottery.getEntranceFee()
    expected_entrance_fee = Web3.toWei(0.025, 'ether')
    # Assert
    assert expected_entrance_fee == entrance_fee


def test_cant_enter_unless_started():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    lottery = deploy_lottery()
    # Act / Assert
    with pytest.raises(exceptions.VirtualMachineError):
        lottery.enter({'from': get_account(), 'value': lottery.getEntranceFee()})


def test_can_start_and_enter_lottery():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    lottery = deploy_lottery()
    account = get_account()
    lottery.startLottery({'from': account})
    # Act
    lottery.enter({'from': get_account(), 'value': lottery.getEntranceFee()+1})
    # Assert
    assert lottery.players(0) == account

def test_can_end_lottery():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    lottery = deploy_lottery()
    account = get_account()
    lottery.startLottery({'from': account})
    lottery.enter({'from': get_account(), 'value': lottery.getEntranceFee()+1})
    fund_with_link(lottery)
    # Act
    lottery.endLottery({'from': account})
    # Assert
    assert lottery.lottery_state() == 2

def test_can_pick_winner_correctly():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    lottery = deploy_lottery()
    account = get_account()
    lottery.startLottery({'from': account})
    lottery.enter({'from': account, 'value': lottery.getEntranceFee()+1})
    lottery.enter({'from': get_account(index=1), 'value': lottery.getEntranceFee()+1})
    lottery.enter({'from': get_account(index=2), 'value': lottery.getEntranceFee()+1})
    fund_with_link(lottery)
    # Act
    transaction = lottery.endLottery({'from': account})
    requestId = transaction.events['RequestedRandomness']['requestId'] # Listen to emitted event
    STATIC_RNG = 777
    get_contract('vrf_coordinator').callBackWithRandomness(
        requestId, STATIC_RNG, lottery.address, {'from': account}
    )
    starting_balance_of_account = account.balance()
    lottery_balance = lottery.balance()
    # Assert
    assert lottery.recentWinner() == account
    assert lottery.balance() == 0
    assert account.balance() == starting_balance_of_account + lottery_balance
    
