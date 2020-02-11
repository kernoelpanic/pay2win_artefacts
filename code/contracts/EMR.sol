pragma solidity <5.5;

import "./SafeMath.sol";
import "./Utils.sol";

contract EMR {
  
    // =================== external Libs =======================
    using SafeMath for uint256;
    using Utils for bytes;
    // =================== end ext. Libs =======================


    // ================ inlined owner handling =================
    address public _owner;
    
    constructor() public {
        _owner = msg.sender;
        _currentState = emrState.deploy;
    }
    
    function owner() public view returns (address) {
        return _owner;
    }

    function isOwner() public view returns (bool) {
        return msg.sender == _owner;
    } 
    // ================ end inl. owner handl. ==================


    // ================== Parseing functions ===================
    /*
     * returns version from Bitcoin block header
     * TODO: nVersion in Bitcoin is actually a int32 not uint32
     * @param byte array of 80 bytes Bitcoin block header
     * @return uint32 version from Bitcoin block header
     */
    function getVersionFromHeader(bytes memory blockHeaderBytes) public pure returns(uint32){
        return uint32(blockHeaderBytes.slice(0,4).flipBytes().bytesToUint()); 
    }
    
    /*
     * returns previous block hash from Bitcoin block header 
     * @param byte array of 80 bytes Bitcoin block header
     * @return bytes32 hashPrevBlock from Bitcoin block header in little endian format 
     */
    function getPrevBlockHash(bytes memory blockHeaderBytes) public pure returns(bytes32){
        return blockHeaderBytes.slice(4, 32).flipBytes().toBytes32();
    }

    /*
     * returns Merkle tree root hash from Bitcoin block header
     * @param byte array of 80 bytes Bitcoin block header
     * @return bytes32 hashMerkleRoot from Bitcoin block header
     */
    function getMerkleRoot(bytes memory blockHeaderBytes) public pure returns(bytes32){
        return blockHeaderBytes.slice(36, 32).flipBytes().toBytes32();
    }

    /* 
     * returns time from Bitcoin block header
     * @param byte array of 80 bytes Bitcoin block header
     * @return uint32 timestamp from Bitcoin block header
     */
    function getTimeFromHeader(bytes memory blockHeaderBytes) public pure returns(uint32){
        return uint32(blockHeaderBytes.slice(68,4).flipBytes().bytesToUint()); 
    }

    /*
     * returns nBits from Bitcoin block header
     * @param byte array of 80 bytes Bitcoin block header
     * @return uint32 nBits from Bitcoin block header 
     */
    function getNBitsFromHeader(bytes memory blockHeaderBytes) public pure returns(uint256){
        return blockHeaderBytes.slice(72, 4).flipBytes().bytesToUint();
    }

    /*
     * returns nonce from Bitcoin block header
     * @param byte array of 80 bytes Bitcoin block header
     * @return uint32 nNonce from Bitcoin block header 
     */
    function getNNonceFromHeader(bytes memory blockHeaderBytes) public pure returns(uint256){
        return blockHeaderBytes.slice(76, 4).flipBytes().bytesToUint();
    }

    /*
     * returns block height from Bitcoin coinbase
     * @param byte array of coinbase
     * @return uint32 block height stored in coinbase 
     */
    function getHeightFromCoinbase(bytes memory coinbaseBytes) public pure returns(uint256){
        uint256 heightLength = coinbaseBytes.slice(0,1).bytesToUint();
        return coinbaseBytes.slice(1,heightLength).flipBytes().bytesToUint();
    }

    /* Extract address from coinbase
     * @param byte array of coinbase
     * @return uint32 block height stored in coinbase 
     */
    function getAddressFromCoinbase(bytes memory coinbaseBytes) public pure returns(address){
        uint256 heightLength = coinbaseBytes.slice(0,1).bytesToUint();
        return address(uint160(coinbaseBytes.slice(1+heightLength,20).flipBytes().bytesToUint()));
    }
    
    /*
     * returns block header with zeroed out Merkle root hash
     * @param byte array of block header
     * @return bytes memory block header with zeroed out Merkle root hash
    */
    function setMerkleRoot(bytes memory blockHeaderBytes) public pure returns(bytes memory) {
      bytes memory blockHeaderBytes_new = new bytes(blockHeaderBytes.length);
      for (uint i = 0; i < blockHeaderBytes.length; i++){
            if ( i >= 36 && i < ( 36 + 32 ) ) {
              blockHeaderBytes_new[i] = byte(0x00);
            } else {
              blockHeaderBytes_new[i] = blockHeaderBytes[i];
            }
      }
      return blockHeaderBytes_new;
    }

    /*
     * returns block header with zeroed out previous block hash
     * @param byte array of block header
     * @return bytes memory block header with zeroed out previous block hash
    */
    function setPrevBlockHash(bytes memory blockHeaderBytes) public pure returns(bytes memory) {
      bytes memory blockHeaderBytes_new = new bytes(blockHeaderBytes.length);
      for (uint i = 0; i < blockHeaderBytes.length; i++){
            if ( i >= 4 && i < ( 4 + 32 ) ) {
              blockHeaderBytes_new[i] = byte(0x00);
            } else {
              blockHeaderBytes_new[i] = blockHeaderBytes[i];
            }
      }
      return blockHeaderBytes_new;
    }
    
    /*
    * @notice Reconstructs merkle tree root given a transaction hash, index in block and merkle tree path
    * @param txIndex index of transaction given by hash in the corresponding block's merkle tree 
    * @param merkleProof merkle tree path to transaction hash from block's merkle tree root
    * @return merkle tree root of the block containing the transaction, meaningless hash otherwise
    */
    function computeMerkle(uint256 txIndex, bytes32 txhash, bytes memory merkleProof) public pure returns(bytes32) {
    
        //  Special case: only coinbase tx in block. Root == proof
        if(merkleProof.length == 32) return merkleProof.toBytes32();

        bytes32 resultHash = txhash;

        for(uint i = 0; i < merkleProof.length / 32; i++) {
            if(txIndex % 2 == 1){
                resultHash = concatSHA256Hash(merkleProof.slice(i * 32, 32), 
                                              abi.encodePacked(resultHash));
            } else {
                resultHash = concatSHA256Hash(abi.encodePacked(resultHash), 
                                              merkleProof.slice(i * 32, 32));
            }
            txIndex /= 2;
        }
        return resultHash;
    }

    /*
    * @notice Concatenates and re-hashes two SHA256 hashes
    * @param left left side of the concatenation
    * @param right right side of the concatenation
    * @return sha256 hash of the concatenation of left and right
    */
    function concatSHA256Hash(bytes memory left, bytes memory right) public pure returns (bytes32) {
        return dblSha(abi.encodePacked(left, right)).toBytes32();
    }

    // ------------------------ Difficutly handling ------------------------
    /*
    * Bitcoin difficulty constants
    */ 
    uint256 public constant DIFFICULTY_ADJUSTMENT_INVETVAL = 2016;

    /*
    * @notice Calculates the PoW difficulty target from compressed nBits representation, 
    * according to https://bitcoin.org/en/developer-reference#target-nbits
    * @param nBits Compressed PoW target representation
    * @return PoW difficulty target computed from nBits
    */
    function nBitsToTarget(uint256 nBits) private pure returns (uint256){
        uint256 exp = uint256(nBits) >> 24;
        uint256 c = uint256(nBits) & 0xffffff;
        uint256 target = uint256((c * 2**(8*(exp - 3))));
        return target;
    }

    function getTargetFromHeader(bytes memory blockHeaderBytes) public pure returns(uint256){
        return nBitsToTarget(getNBitsFromHeader(blockHeaderBytes));
    }
    /*
    function getDifficulty(uint256 target) public pure returns(uint256){
        return 0x00000000FFFF0000000000000000000000000000000000000000000000000000 / target;
    } 
    */
    // -------------------- end difficulty handling ------------------------
    // ==================== end parseing functions =========================


    // ======================= helper functions ============================

    /*
    * @notice Performns Bitcoin-like double sha256 (LE!)
    * @param data Bytes to be flipped and double hashed s
    * @return Reversed and double hashed representation of parsed data
    */
    function dblShaFlip(bytes memory data) public pure returns (bytes memory){
        return abi.encodePacked(sha256(abi.encodePacked(sha256(data)))).flipBytes();
    }

    function dblSha(bytes memory data) public pure returns (bytes memory){
        return abi.encodePacked(sha256(abi.encodePacked(sha256(data))));
    }

    // ====================== end helper functions =========================


    // ============================= EMR ===================================

    enum emrState { deploy, init, attack, payout } // possible states of the EMR
    emrState public _currentState; // current state of EMR, initialized in constructor

    uint256 public _startHeight;
    uint256 public _kV;
    uint256 public _kB;
    bytes32 public _startHash;
    bool public _attackSuccessful;

    uint256 public _remaining_init_cblocks;
    uint256 public _remaining_init_tblocks;

    bytes32 public _current_leading_hash;
    uint256 public _current_leading_height;

    bytes32 public _current_leading_attack_hash;
    uint256 public _current_leading_attack_height;

    uint256 public _number_tblocks;
    uint256 public _number_cblocks;

    bool public constant TEST = true; // Set if contract runs in test mode, does not actually verify PoW  
    uint256 public constant TARGET = 0x896c00000000000000000000000000000000000000000000; // Hard coded target for current 2016 (2016-1) blocks

    struct TemplateBlock {
        uint256 blockHeight; // Height at which this block shoudl occure
        uint256 blockReward; // Reward to pay for this block
        uint256 blockBribe;  // Bribe to pay for this block
        bytes32 tblockHash;  // Block header with merkle-tree hash set to all zeros
        bytes32 merklePath_hash; // hash of the submitted merkle path to later verify rblock
        bytes32 blockCoinbase_prefix_hash; // hash of the submitted prefix and suffix of coinbase to verify rbock later
        bytes32 blockCoinbase_suffix_hash;
        bool mined; // indicator if a block complying to this template has been mined
        bytes32 blockHash;
    }
    mapping(uint256 => TemplateBlock) public _tblocks; //maps height to template block

    struct CompensationBlock {
        bytes32 blockHash; // hash of this block header (can be calculated from header)
        bytes32 prevBlockHash; // (in header)
        uint256 blockHeight; // (in header)
        uint256 blockReward; 
        address payable blockMiner; // miner payout account, lets assume we know this for the first k_V mainchain blocks
    }
    mapping(uint256 => CompensationBlock) public _cblocks; 

    struct ReceivedBlock {
        bytes32 blockHash; // hash of this block header (can be calculated from header)
        bytes32 prevBlockHash; // (in header)
        uint256 blockHeight; // (in header)
        address payable blockMiner; // miner payout account, not relevant for main chain blocks
        uint256 tblockHeight; // if mined according to template, this is non-zero, zero if main chain
    }
    mapping(bytes32 => ReceivedBlock) public _rblocks; 

    mapping(address => uint256) public _payouts;

    // ============================= EMR func. ===================================
    /*
     * @param startHeight the block height of the target chain when attack starts
     * @param kV Security parameter of the victim, i.e., number of blocks on the main chain
     * @param kB Security parameter of the attacker, i.e., number of block to wait after the attack has reached k_V blocks till received chain considered final 
     * @param startHash s
     */ 
    function initEMR(uint256 startHeight, 
                     uint256 kV, 
                     uint256 kB, 
                     bytes32 startHash) external {
      require(msg.sender == _owner,"Wrong user");
      require(_currentState == emrState.deploy,"Wrong state");

      _startHeight = startHeight;
      _kV = kV;
      _kB = kB;
      _startHash = startHash;
      _attackSuccessful = false;

      _current_leading_hash = startHash;
      _current_leading_height = startHeight;

      _current_leading_attack_hash = startHash;
      _current_leading_attack_height = startHeight;

      //remaining blocks for initialization till attack starts 
      _remaining_init_cblocks = kV;  
      _remaining_init_tblocks = kV+1;
      _number_tblocks = 0;
      _number_cblocks = 0;

      _currentState = emrState.init; // we are now in init state and wait for k_V cblocks and k_V+1 tblocks 
      emit Init_start(_startHeight,_kV,_startHash);
    }

    event Init_start(
      uint256 indexed _startHeight,
      uint256 indexed _kV,
      bytes32 indexed _startHash
    );

    function get_currentState() public view returns(uint256) {
      return uint256(_currentState);
    }

    function submit_cblock(bytes calldata cblock,
                           uint256 blockHeight,
                           uint256 blockReward, 
                           address payable blockMiner) payable external {
      require(msg.sender == _owner, "Only owner");
      require(_currentState == emrState.init,"Wrong state");
      require(_remaining_init_cblocks > 0, "Enough cblocks");
      
      bool valid = true;
      CompensationBlock memory cb;
      cb.blockHash = dblSha(cblock.slice(0,80)).flipBytes().toBytes32();
      cb.prevBlockHash = getPrevBlockHash(cblock);
      cb.blockHeight = blockHeight;
      cb.blockMiner = blockMiner;
      cb.blockReward = blockReward;
      //check if prevBlock exsits already
      if ( _startHeight+1 == cb.blockHeight ) {
          require(_startHash == cb.prevBlockHash,"Previous hash not startHash");
      } else {
          //require(_cblocks[cb.prevBlockHash].blockHeight == cb.blockHeight - 1,"Wrong Height");
          require(_cblocks[cb.blockHeight - 1].blockHash == cb.prevBlockHash);
      }

      if ( valid ) {
        _cblocks[cb.blockHeight] = cb;
        _current_leading_hash = cb.blockHash;
        _current_leading_height = cb.blockHeight;
        _remaining_init_cblocks = _remaining_init_cblocks - 1;
        _number_cblocks = _number_cblocks + 1;
        emit Valid_cblock(msg.sender,cb.blockHash,cb.prevBlockHash); //TODO: change event and remove msg.sender to save gas
      }
    }

    event Valid_cblock(
      address indexed _from,
      bytes32 indexed _blockHash,
      bytes32 indexed _prevBlockHash
    );

    function submit_tblock(bytes calldata tblock,
                           bytes calldata blockCoinbase_prefix,
                           uint256 blockHeight,
                           bytes calldata blockCoinbase_suffix,
                           bytes calldata merklePath,
                           uint256 blockReward,
                           uint256 blockBribe) payable external {
      require(msg.sender == _owner);
      
      if ( _currentState == emrState.deploy ) {
        revert("EMR initialization not yet started");
      }

      if ( _currentState == emrState.payout ) {
        revert("Already in payout phase no more blocks required");
      }

      if ( _currentState == emrState.init ) {
        if ( _remaining_init_tblocks == 0 && _remaining_init_cblocks == 0 ) {
          //in case some cblocks have been missing but we had all tblocks already
          //move to attack phase if missing cblocks are here now
          _currentState = emrState.attack;
        } 
        if ( _remaining_init_tblocks > 0 ) {
          require(uint256(getMerkleRoot(tblock)) == 0x0,"Merkle Root must be zero for template"); 
          require(uint256(getPrevBlockHash(tblock)) == 0x0,"Previous hash must be zero for template"); 
          TemplateBlock memory tb;
          tb.blockHeight = blockHeight;
          tb.blockReward = blockReward;
          tb.blockBribe = blockBribe;
          tb.mined = false;
          // compute hashe of tblock header, with merkle-tree root set to all zeros for later comparison
          tb.tblockHash = dblSha(tblock.slice(0,80)).flipBytes().toBytes32();

          // store blockChainbase_prefix and _suffix hashes to later verify submitted ones
          // Full version needs to be submitted to be emitted via event and allow for mining
          tb.blockCoinbase_prefix_hash = dblSha(blockCoinbase_prefix).flipBytes().toBytes32();
          tb.blockCoinbase_suffix_hash = dblSha(blockCoinbase_suffix).flipBytes().toBytes32();

          // store merklePath_hash to later check validity submitted one and check validity 
          // Full version needs to be submitted to be emitted via event and allow for mining
          tb.merklePath_hash = dblSha(merklePath).flipBytes().toBytes32();

          // emit event broadcasting the values
          emit New_tblock(tb.blockHeight,
                          tb.blockReward,
                          tb.blockBribe,
                          tblock,
                          blockCoinbase_prefix,
                          blockCoinbase_suffix,
                          merklePath);

          // do not allow overwriting existing tblock (yet, maybe only if bribe is higher and not yet mined.) 
          require(_tblocks[tb.blockHeight].blockHeight == 0,"tblock must not be overwritten");
          _tblocks[tb.blockHeight] = tb;
          _number_tblocks = _number_tblocks + 1;
          
          // Ony in this phase relevant:
          _remaining_init_tblocks = _remaining_init_tblocks - 1;
          if ( _remaining_init_tblocks == 0 && _remaining_init_cblocks == 0 ) {
            //Check if we are done initializing yet, if so move to attack phase
            _currentState = emrState.attack;  
          }
          return;
        } 
      }
      if ( _currentState == emrState.attack ) {
        // Extend currently running attack by one more (t)block
        revert("Not yet implemented");
        // Same code as above:
        // - check if tblock header merkle-tree is all zeros
        // - compute and store hashes of tblock data, with merkle-tree root set to all zeros
        // - store height
        // - store blockChainbase_prefix and _suffix 
        // - emit event broadcasting the values 

        // New and only in this phase relevant:
        // - increase kV
        return;
      }
    }

    function get_tblock_data(uint256 blockHeight) public view returns(bool _mined,
                                                                      uint256 _blockReward,
                                                                      uint256 _blockBribe,
                                                                      bytes32 _tblockHash,
                                                                      bytes32 _merklePath_hash,
                                                                      bytes32 _blockCoinbase_prefix_hash,
                                                                      bytes32 _blockCoinbase_suffix_hash){
      TemplateBlock memory tb = _tblocks[blockHeight];
      _mined = tb.mined;
      _blockReward = tb.blockReward;
      _blockBribe = tb.blockBribe;
      _tblockHash = tb.tblockHash;
      _merklePath_hash = tb.merklePath_hash;
      _blockCoinbase_prefix_hash = tb.blockCoinbase_prefix_hash;
      _blockCoinbase_suffix_hash = tb.blockCoinbase_suffix_hash;
    }

    event New_tblock(
      uint256 indexed _blockHeight,
      uint256 indexed _blockReward,
      uint256 indexed _blockBribe,
      bytes _tblockHeader,
      bytes _blockCoinbase_prefix,
      bytes _blockCoinbase_suffix,
      bytes _merklePath
    );

    function submit_rblock(bytes calldata rblock, 
                           bytes calldata blockCoinbase, 
                           bytes calldata blockCoinbase_prefix,
                           bytes calldata blockCoinbase_suffix,
                           bytes calldata merklePath) external {
      require( _currentState == emrState.attack, "Not in attack phase" );
      
      ReceivedBlock memory rb;   
      rb.blockHash = dblShaFlip(rblock).toBytes32();
      rb.prevBlockHash = getPrevBlockHash(rblock);
      rb.blockMiner = msg.sender;

      uint256 target = getTargetFromHeader(rblock);
      if ( TEST == false ) { 
        // If not in TEST mode:
        // Check the PoW solution matches the target specified in the block header 
        // Since header cannot be changed due to later tblock check, 
        // this should be sufficient for blocks mined according to tblock template
        require(rb.blockHash <= bytes32(target), "Difficulty of block to low");
        // For main chain blocks we assume a fixed target for now:
        require(target == TARGET,"Wrong Target");      
        // Extract address from coinbase and compare with msg.sender to 
        // protect against replay attacks:
        require(msg.sender == getAddressFromCoinbase(blockCoinbase),"msg.sender not in coinbase");
      } 

      // extract height from coinbase:
      rb.blockHeight = getHeightFromCoinbase(blockCoinbase);
      
      // set merkle-tree to all zeros and compare to tblock at hight
      //bytes memory tblock = setMerkleRoot(rblock);  //inlined 
      //bytes32 tblockHash = dblShaFlip(tblock).toBytes32(); //inlined
      
      TemplateBlock memory tb = _tblocks[rb.blockHeight];
      //if ( tb.tblockHash == tblockHash) {
      if ( tb.tblockHash == dblShaFlip(setPrevBlockHash(setMerkleRoot(rblock))).toBytes32()) {
        // Block is from attack chain with a template:
        require(tb.mined == false,"No block at hight"); // check if we have some block at that hight already 
                
        // only allow sequential submissions 
        if ( _current_leading_attack_height == _startHeight ) {
          require(_startHash == rb.prevBlockHash, "Not valid first attack chain block");
        } else {
          require(_rblocks[rb.prevBlockHash].blockHeight == rb.blockHeight-1, "Submitted block not sequential");
        }

        // Check if prefix and suffix are correct
        require(tb.blockCoinbase_prefix_hash == dblSha(blockCoinbase_prefix).flipBytes().toBytes32(),"Pfx check false");
        require(tb.blockCoinbase_suffix_hash == dblSha(blockCoinbase_suffix).flipBytes().toBytes32(),"Sfx check false");
        // Check if merkle path is correct
        require(tb.merklePath_hash == dblSha(merklePath).flipBytes().toBytes32(),"Merkle path check false");
        // Check if merkle root hash is correct
        bytes32 merkleRoot = abi.encodePacked(getMerkleRoot(rblock)).flipBytes().toBytes32();
        bytes memory coinbaseTx = new bytes(blockCoinbase.length + 
                               blockCoinbase_prefix.length +
                               blockCoinbase_suffix.length);
        for (uint i = 0; i < blockCoinbase_prefix.length; i++) {
           coinbaseTx[i] = blockCoinbase_prefix[i];
        }
        for (uint i = 0; i < blockCoinbase.length; i++) {
           coinbaseTx[i + blockCoinbase_prefix.length] = blockCoinbase[i];
        }
        for (uint i = 0; i < blockCoinbase_suffix.length; i++) {
           coinbaseTx[i + blockCoinbase_prefix.length + blockCoinbase.length] = blockCoinbase_suffix[i];
        }
        bytes32 coinbaseTx_hash = dblSha(coinbaseTx).toBytes32();
        require(merkleRoot == computeMerkle(0, coinbaseTx_hash, merklePath),"Merkle Root mismatch");
        
        // add new attack chain block mined according to template
        tb.mined = true;
        tb.blockHash = rb.blockHash;
        _tblocks[rb.blockHeight] = tb;
        rb.tblockHeight = rb.blockHeight; 
        _rblocks[rb.blockHash] = rb;

        if ( _current_leading_attack_height < rb.blockHeight ) {
          _current_leading_attack_height = rb.blockHeight;
          _current_leading_attack_hash = rb.blockHash;
        }
      
      } else {
        // Either Block is from some other/main chain, or
        // block is from the attack chain after attack has succeeded 
        
        //only allow sequential submissions
        bool foundPrev = false;
        if (rb.blockHeight == _startHeight+1 ) {
          require(_startHash == rb.prevBlockHash,"Invalid previous start hash");
          foundPrev = true;
        }

        if ( foundPrev == false) {
          for (uint i = _startHeight + 1; i < (_startHeight + 1 + _number_cblocks);i++) {
            if ( _cblocks[i].blockHash == rb.prevBlockHash) {
              require(_cblocks[i].blockHeight == rb.blockHeight-1,"Invalid previous cblock height");
              foundPrev = true;
            }
          }
        }
        if ( foundPrev == false ) {
          require(_rblocks[rb.prevBlockHash].blockHeight == rb.blockHeight - 1, "Submitted block has no valid previous");
        }

        // add new block
        rb.tblockHeight = 0; // its not a block mined according to template
        _rblocks[rb.blockHash] = rb;
      }
      require(_rblocks[rb.blockHash].blockHeight != 0,"No Block"); // safty check, must have an added block here

      emit New_rblock(rb.blockHash,
                      rb.blockHeight,
                      tb.tblockHash,
                      blockCoinbase,
                      blockCoinbase_prefix,
                      blockCoinbase_suffix,
                      merklePath);

      // check if new block is the new leader general lead, update:
      if ( _current_leading_height < rb.blockHeight ) {
        _current_leading_height = rb.blockHeight;
        _current_leading_hash = rb.blockHash;
      }

      // check if we are done yet, i.e., kV+1 reached and k_B blocks on top of that
      if ( _current_leading_height >= _startHeight + _kV + 1 + _kB ) {
        _currentState = emrState.payout;
        computePayouts();
      }
    }

    /*
     * TODO: Actually the last three values should be same as in tblock, can be omitted to save gas
     */
    event New_rblock(
      bytes32 indexed _rblockHash,
      uint256 indexed _blockHeight,
      bytes32 indexed _tblockHash,
      bytes _blockCoinbase,
      bytes _blockCoinbase_prefix,
      bytes _blockCoinbase_suffix,
      bytes _merklePath
    );

    function computePayouts() private {
      //bool attackSuccessful = false;
      ReceivedBlock memory rb = _rblocks[_current_leading_hash];
      while ( rb.blockHeight != 0) {
        // when we hit a block with tblockHeight at height _kV+1 
        // the attack chain won, otherwise main chain won
        if ( rb.blockHeight == _startHeight + _kV + 1) {
          if ( rb.tblockHeight != 0 ) {
            _attackSuccessful = true;
          }
        }
        if ( rb.blockHeight <= _startHeight + _kV + 1) {
          if ( _attackSuccessful == true ) {
            assert( rb.tblockHeight != 0 ); // safty check, there must be tblocks for every rblock now
            _payouts[rb.blockMiner] += _tblocks[rb.tblockHeight].blockReward + _tblocks[rb.tblockHeight].blockBribe;
          }
        }
        rb = _rblocks[rb.prevBlockHash];
      }
      if ( _attackSuccessful == true ) {
        CompensationBlock memory cb;
        for (uint i = _startHeight + 1; i <= ( _startHeight + _number_cblocks);i++) {
          cb = _cblocks[i];
          _payouts[cb.blockMiner] += cb.blockReward;
        }
      } else {
        TemplateBlock memory tb;
        for (uint i = _startHeight + 1; i <= ( _startHeight + _number_tblocks);i++) {
          tb = _tblocks[i];
          if (tb.mined == true) {
            ReceivedBlock memory rm = _rblocks[tb.blockHash];
            _payouts[rm.blockMiner] += tb.blockReward;
          }
        }
      }
      return;  
    }

    function payout() external {
      require(_currentState == emrState.payout, "Not in payout phase yet");
      uint256 amount = _payouts[msg.sender];
      if ( amount > 0) {
        msg.sender.transfer(amount);
        _payouts[msg.sender] = 0;
        //emit Payed(msg.sender,amount);
      }
    }
    /*
    event Payed(
      address indexed _to,
      uint256 indexed _amount
    );
    */

    //TODO: 
    // * Remove strings from revert() and requires() to save gas
    // * Remove invalid events to save gas
}
