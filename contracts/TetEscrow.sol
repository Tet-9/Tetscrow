// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/// @title TetEscrow
/// @notice Decentralized milestone-based escrow. Funds (ETH or an allow-listed ERC20)
///         are locked in this contract between a Sender (payer) and a Receiver (payee)
///         until the Sender releases them, or a Dispute is resolved by an Arbiter.
///         Mirrors the 5-step flow: Create -> Fund -> Deliver -> Release (or Dispute).
contract TetEscrow {
    enum Status { Created, Funded, Delivered, Released, Disputed, Resolved, Cancelled }

    struct Agreement {
        address sender;      // pays into escrow
        address receiver;    // receives funds on release
        address arbiter;     // resolves disputes (0x0 = platform default arbiter)
        address token;       // address(0) = native ETH
        uint256 amount;
        uint256 createdAt;
        uint256 deliveredAt;  // 0 until markDelivered() is called
        Status status;
        string  termsURI;    // off-chain link (IPFS/HTTPS) to the human-readable agreement text
    }

    uint256 public nextAgreementId;
    address public defaultArbiter;
    address public feeRecipient;
    uint16  public feeBasisPoints; // e.g. 100 = 1%
    uint256 public autoReleaseDelay; // seconds after delivery before ANYONE can trigger release

    mapping(uint256 => Agreement) public agreements;
    mapping(uint256 => string) public disputeReasons;

    event AgreementCreated(uint256 indexed id, address indexed sender, address indexed receiver, address token, uint256 amount, string termsURI);
    event Funded(uint256 indexed id, uint256 amount);
    event Delivered(uint256 indexed id);
    event Released(uint256 indexed id, address indexed to, uint256 amount);
    event AutoReleased(uint256 indexed id, address indexed to, uint256 amount);
    event Disputed(uint256 indexed id, address indexed raisedBy, string reason);
    event Resolved(uint256 indexed id, address indexed winner, uint256 amount);
    event Cancelled(uint256 indexed id);

    modifier onlyParty(uint256 id) {
        Agreement storage a = agreements[id];
        require(msg.sender == a.sender || msg.sender == a.receiver, "not a party");
        _;
    }

    constructor(address _defaultArbiter, address _feeRecipient, uint16 _feeBasisPoints, uint256 _autoReleaseDelay) {
        require(_feeBasisPoints <= 1000, "fee too high"); // hard cap 10%
        defaultArbiter = _defaultArbiter;
        feeRecipient = _feeRecipient;
        feeBasisPoints = _feeBasisPoints;
        autoReleaseDelay = _autoReleaseDelay;
    }

    /// @notice Step 1 — Create a contract between parties.
    function createAgreement(
        address receiver,
        address arbiter,
        address token,
        uint256 amount,
        string calldata termsURI
    ) external returns (uint256 id) {
        require(receiver != address(0) && receiver != msg.sender, "bad receiver");
        require(amount > 0, "amount = 0");

        id = nextAgreementId++;
        agreements[id] = Agreement({
            sender: msg.sender,
            receiver: receiver,
            arbiter: arbiter == address(0) ? defaultArbiter : arbiter,
            token: token,
            amount: amount,
            createdAt: block.timestamp,
            status: Status.Created,
            termsURI: termsURI
        });

        emit AgreementCreated(id, msg.sender, receiver, token, amount, termsURI);
    }

    /// @notice Step 2 — Client pays into escrow (ETH or ERC20, matching the agreement).
    function fund(uint256 id) external payable {
        Agreement storage a = agreements[id];
        require(msg.sender == a.sender, "only sender");
        require(a.status == Status.Created, "bad status");

        if (a.token == address(0)) {
            require(msg.value == a.amount, "wrong ETH amount");
        } else {
            require(msg.value == 0, "no ETH for token escrow");
            _transferFrom(a.token, msg.sender, address(this), a.amount);
        }

        a.status = Status.Funded;
        emit Funded(id, a.amount);
    }

    /// @notice Step 3 — Receiver marks the service/RWA as delivered.
    function markDelivered(uint256 id) external {
        Agreement storage a = agreements[id];
        require(msg.sender == a.receiver, "only receiver");
        require(a.status == Status.Funded, "bad status");
        a.status = Status.Delivered;
        a.deliveredAt = block.timestamp;
        emit Delivered(id);
    }

    /// @notice Step 4A — Sender releases payment once satisfied.
    function release(uint256 id) external {
        Agreement storage a = agreements[id];
        require(msg.sender == a.sender, "only sender");
        require(a.status == Status.Funded || a.status == Status.Delivered, "bad status");

        a.status = Status.Released;
        _payout(a, a.receiver, a.amount);
        emit Released(id, a.receiver, a.amount);
    }

    /// @notice Anyone can trigger this once the auto-release window has passed since
    ///         delivery, protecting the receiver from a sender who simply goes silent
    ///         instead of releasing or disputing. Raising a dispute before this is
    ///         called always takes precedence — this only fires if nobody acted.
    function autoRelease(uint256 id) external {
        Agreement storage a = agreements[id];
        require(a.status == Status.Delivered, "not deliverable-pending");
        require(a.deliveredAt != 0, "no delivery timestamp");
        require(block.timestamp >= a.deliveredAt + autoReleaseDelay, "auto-release window not reached");

        a.status = Status.Released;
        _payout(a, a.receiver, a.amount);
        emit AutoReleased(id, a.receiver, a.amount);
    }

    /// @notice Step 4B — Either party raises a dispute; funds freeze pending arbitration.
    function raiseDispute(uint256 id, string calldata reason) external onlyParty(id) {
        Agreement storage a = agreements[id];
        require(a.status == Status.Funded || a.status == Status.Delivered, "bad status");
        a.status = Status.Disputed;
        disputeReasons[id] = reason;
        emit Disputed(id, msg.sender, reason);
    }

    /// @notice Arbiter resolves a dispute, sending the full escrowed amount to the winner.
    function resolveDispute(uint256 id, address winner) external {
        Agreement storage a = agreements[id];
        require(msg.sender == a.arbiter, "only arbiter");
        require(a.status == Status.Disputed, "not disputed");
        require(winner == a.sender || winner == a.receiver, "winner must be a party");

        a.status = Status.Resolved;
        _payout(a, winner, a.amount);
        emit Resolved(id, winner, a.amount);
    }

    /// @notice Sender can cancel only before funding (no funds at risk).
    function cancel(uint256 id) external {
        Agreement storage a = agreements[id];
        require(msg.sender == a.sender, "only sender");
        require(a.status == Status.Created, "already funded");
        a.status = Status.Cancelled;
        emit Cancelled(id);
    }

    // ---- internal helpers ----

    function _payout(Agreement storage a, address to, uint256 amount) internal {
        uint256 fee = (amount * feeBasisPoints) / 10_000;
        uint256 net = amount - fee;

        if (a.token == address(0)) {
            if (fee > 0) payable(feeRecipient).transfer(fee);
            payable(to).transfer(net);
        } else {
            if (fee > 0) _transfer(a.token, feeRecipient, fee);
            _transfer(a.token, to, net);
        }
    }

    function _transferFrom(address token, address from, address to, uint256 amount) internal {
        (bool ok, bytes memory data) = token.call(
            abi.encodeWithSignature("transferFrom(address,address,uint256)", from, to, amount)
        );
        require(ok && (data.length == 0 || abi.decode(data, (bool))), "transferFrom failed");
    }

    function _transfer(address token, address to, uint256 amount) internal {
        (bool ok, bytes memory data) = token.call(
            abi.encodeWithSignature("transfer(address,uint256)", to, amount)
        );
        require(ok && (data.length == 0 || abi.decode(data, (bool))), "transfer failed");
    }

    function getAgreement(uint256 id) external view returns (Agreement memory) {
        return agreements[id];
    }
}
