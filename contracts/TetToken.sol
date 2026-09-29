// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/// @title TetToken ($TET)
/// @notice Plain, transparent ERC-20. Fixed total supply minted once to `initialHolder`
///         at deploy time (your own wallet) — no hidden owner mint function, no
///         blacklist/pause backdoor, no ability to alter balances after deployment.
///         This is intentionally "boring": whatever trust the token earns should come
///         from what the escrow platform actually does, not from contract tricks.
contract TetToken {
    string public constant name = "Tet";
    string public constant symbol = "TET";
    uint8  public constant decimals = 18;
    uint256 public immutable totalSupply;

    mapping(address => uint256) public balanceOf;
    mapping(address => mapping(address => uint256)) public allowance;

    event Transfer(address indexed from, address indexed to, uint256 value);
    event Approval(address indexed owner, address indexed spender, uint256 value);

    constructor(uint256 totalSupply_, address initialHolder) {
        require(initialHolder != address(0), "bad holder");
        totalSupply = totalSupply_;
        balanceOf[initialHolder] = totalSupply_;
        emit Transfer(address(0), initialHolder, totalSupply_);
    }

    function transfer(address to, uint256 amount) external returns (bool) {
        _transfer(msg.sender, to, amount);
        return true;
    }

    function approve(address spender, uint256 amount) external returns (bool) {
        allowance[msg.sender][spender] = amount;
        emit Approval(msg.sender, spender, amount);
        return true;
    }

    function transferFrom(address from, address to, uint256 amount) external returns (bool) {
        uint256 allowed = allowance[from][msg.sender];
        require(allowed >= amount, "allowance exceeded");
        if (allowed != type(uint256).max) {
            allowance[from][msg.sender] = allowed - amount;
        }
        _transfer(from, to, amount);
        return true;
    }

    function _transfer(address from, address to, uint256 amount) internal {
        require(to != address(0), "transfer to zero");
        uint256 bal = balanceOf[from];
        require(bal >= amount, "insufficient balance");
        unchecked {
            balanceOf[from] = bal - amount;
            balanceOf[to] += amount;
        }
        emit Transfer(from, to, amount);
    }
}
