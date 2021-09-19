// SPDX-License-Identifier: MIT

pragma solidity ^0.6.6;

import '@chainlink/contracts/src/v0.6/interfaces/AggregatorV3Interface.sol';
import '@openzeppelin/contracts/access/Ownable.sol';
import '@chainlink/contracts/src/v0.6/VRFConsumerBase.sol';

contract Lottery is VRFConsumerBase, Ownable { // Inherit from VRFConsumerBase and Ownable

    address payable[] public players; // Init array of payable addresses
    address payable  public recentWinner; // Init payable recent winner address 
    uint256 public randomness; // Init a variable for randomness
    uint256 public usdEntryFee; // Init a var to set the entry fee
    uint256 public fee; // Init a var for tx fee 
    bytes32 public keyhash; // Init a var for the key hash


    AggregatorV3Interface internal ethUsdPriceFeed; // Init internal interface var
    enum LOTTERY_STATE {OPEN, CLOSED, CALCULATING_WINNER} // init new data type to keep track of the state of the lottery
    LOTTERY_STATE public lottery_state; // Init the state as a variable
    event RequestedRandomness(bytes32 requestId); // Init an event to emit later
    

    // Constructor function called at deployment
    // Set some vars at deployment
    constructor (address _priceFeedAddress, address _vrfCoordinator, address _link, uint256 _fee, bytes32 _keyhash) 
        public 
        VRFConsumerBase(_vrfCoordinator, _link) 
        {
            usdEntryFee = 50 * (10**18);
            ethUsdPriceFeed = AggregatorV3Interface(_priceFeedAddress);
            lottery_state = LOTTERY_STATE.CLOSED;
            fee = _fee;
            keyhash = _keyhash;
        }

    function enter() public payable { // Function to enter the lottery
        // $50 min
        require(lottery_state == LOTTERY_STATE.OPEN, 'The lottery is not open at this time'); // Check lottery is open 
        require(msg.value > getEntranceFee(), 'You need at least $50 to enter'); // Check person paid sufficient funds
        players.push(msg.sender); // Add msg.sender to array of players
    }
    function getEntranceFee() public view returns (uint256) { // Function to get entrance fee
        (, int256 price, , , ) = ethUsdPriceFeed.latestRoundData(); // get latest eth/usd price
        uint256 adjustedPrice = uint256(price) * 10**10; // Adjust price to correct decimals
        uint256 costToEnter = (usdEntryFee * 10**18) / adjustedPrice; // Find USD cost to enter
        return costToEnter; // return cost to enter
    }

    function startLottery() public onlyOwner { // Function to start the lottery
        require(lottery_state == LOTTERY_STATE.CLOSED, 'Cannot start new lottery yet'); // Check state of lottery 
        lottery_state = LOTTERY_STATE.OPEN; // set state of lottery
    }
    function endLottery() public onlyOwner returns (address) { // Function to end lottery
        lottery_state = LOTTERY_STATE.CALCULATING_WINNER; // set the lottery state to calculating winner state 
        bytes32 requestId = requestRandomness(keyhash, fee); // Get a random number
        emit RequestedRandomness(requestId); // fire off an event
    }

    function fulfillRandomness(bytes32 _requestId, uint256 _randomness) internal override { // Function to get random number
        require(lottery_state == LOTTERY_STATE.CALCULATING_WINNER, 'Lottery needs to be calculating a winner to fire this function'); // check state of lottery 
        require(_randomness > 0, 'Randomness not initialized'); // Check randomness is random
        uint256 indexOfWinner = _randomness % players.length; // Get winner index by dividing random number by length of players array
        recentWinner = players[indexOfWinner]; // set recent winner var
        recentWinner.transfer(address(this).balance); // transfer winnings to winner
        // Reset  
        players = new address payable[](0); // Clear players array
        lottery_state = LOTTERY_STATE.CLOSED; // set lottery state to closed  
        randomness = _randomness; // set randomness var
    }
}