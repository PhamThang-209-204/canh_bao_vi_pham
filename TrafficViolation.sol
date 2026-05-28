// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract TrafficViolation {
    struct Violation {
        uint256 vehicleId;
        string speed;
        string timestamp;
        string imageHash;
    }

    // Mapping from a unique violation ID to a Violation struct
    mapping(string => Violation) public violations;

    event ViolationAdded(string indexed violationId, uint256 vehicleId, string speed, string timestamp, string imageHash);

    // Add a new violation
    function addViolation(
        string memory _violationId,
        uint256 _vehicleId,
        string memory _speed,
        string memory _timestamp,
        string memory _imageHash
    ) public {
        violations[_violationId] = Violation({
            vehicleId: _vehicleId,
            speed: _speed,
            timestamp: _timestamp,
            imageHash: _imageHash
        });

        emit ViolationAdded(_violationId, _vehicleId, _speed, _timestamp, _imageHash);
    }

    // Retrieve a violation by its ID
    function getViolation(string memory _violationId) public view returns (
        uint256 vehicleId,
        string memory speed,
        string memory timestamp,
        string memory imageHash
    ) {
        Violation memory v = violations[_violationId];
        return (v.vehicleId, v.speed, v.timestamp, v.imageHash);
    }
}
