// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract FileLog {
    struct File {
        address user;
        string filename;
        uint256 timestamp;
    }

    File[] public files;

    event FileUploaded(address indexed user, string filename, uint256 timestamp);

    function logFile(string memory _filename) public {
        files.push(File(msg.sender, _filename, block.timestamp));
        emit FileUploaded(msg.sender, _filename, block.timestamp);
    }

    function getFiles() public view returns (File[] memory) {
        return files;
    }
}
