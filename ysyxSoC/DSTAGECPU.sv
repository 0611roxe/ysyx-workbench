module DSTAGECPU(
  input         clock,
                reset,
                io_master_awready,
  output        io_master_awvalid,
  output [3:0]  io_master_awid,
  output [31:0] io_master_awaddr,
  output [7:0]  io_master_awlen,
  output [2:0]  io_master_awsize,
  output [1:0]  io_master_awburst,
  input         io_master_wready,
  output        io_master_wvalid,
  output [31:0] io_master_wdata,
  output [3:0]  io_master_wstrb,
  output        io_master_wlast,
                io_master_bready,
  input         io_master_bvalid,
  input  [3:0]  io_master_bid,
  input  [1:0]  io_master_bresp,
  input         io_master_arready,
  output        io_master_arvalid,
  output [3:0]  io_master_arid,
  output [31:0] io_master_araddr,
  output [7:0]  io_master_arlen,
  output [2:0]  io_master_arsize,
  output [1:0]  io_master_arburst,
  output        io_master_rready,
  input         io_master_rvalid,
  input  [3:0]  io_master_rid,
  input  [31:0] io_master_rdata,
  input  [1:0]  io_master_rresp,
  input         io_master_rlast,
                io_interrupt,
  output        io_slave_awready,
  input         io_slave_awvalid,
  input  [3:0]  io_slave_awid,
  input  [31:0] io_slave_awaddr,
  input  [7:0]  io_slave_awlen,
  input  [2:0]  io_slave_awsize,
  input  [1:0]  io_slave_awburst,
  output        io_slave_wready,
  input         io_slave_wvalid,
  input  [31:0] io_slave_wdata,
  input  [3:0]  io_slave_wstrb,
  input         io_slave_wlast,
                io_slave_bready,
  output        io_slave_bvalid,
  output [3:0]  io_slave_bid,
  output [1:0]  io_slave_bresp,
  output        io_slave_arready,
  input         io_slave_arvalid,
  input  [3:0]  io_slave_arid,
  input  [31:0] io_slave_araddr,
  input  [7:0]  io_slave_arlen,
  input  [2:0]  io_slave_arsize,
  input  [1:0]  io_slave_arburst,
  input         io_slave_rready,
  output        io_slave_rvalid,
  output [3:0]  io_slave_rid,
  output [31:0] io_slave_rdata,
  output [1:0]  io_slave_rresp,
  output        io_slave_rlast
);

  wire [31:0] _bridge_io_ifu_rdata;
  wire        _bridge_io_ifu_respValid;
  wire [31:0] _bridge_io_lsu_rdata;
  wire        _bridge_io_lsu_respValid;
  wire [31:0] _cpu_io_ifu_addr;
  wire        _cpu_io_ifu_reqValid;
  wire [31:0] _cpu_io_lsu_addr;
  wire        _cpu_io_lsu_reqValid;
  wire [1:0]  _cpu_io_lsu_size;
  wire        _cpu_io_lsu_wen;
  wire [31:0] _cpu_io_lsu_wdata;
  wire [3:0]  _cpu_io_lsu_wmask;
  ysyx_00000000 cpu (
    .clock            (clock),
    .reset            (reset),
    .io_ifu_addr      (_cpu_io_ifu_addr),
    .io_ifu_reqValid  (_cpu_io_ifu_reqValid),
    .io_ifu_rdata     (_bridge_io_ifu_rdata),
    .io_ifu_respValid (_bridge_io_ifu_respValid),
    .io_lsu_addr      (_cpu_io_lsu_addr),
    .io_lsu_reqValid  (_cpu_io_lsu_reqValid),
    .io_lsu_rdata     (_bridge_io_lsu_rdata),
    .io_lsu_respValid (_bridge_io_lsu_respValid),
    .io_lsu_size      (_cpu_io_lsu_size),
    .io_lsu_wen       (_cpu_io_lsu_wen),
    .io_lsu_wdata     (_cpu_io_lsu_wdata),
    .io_lsu_wmask     (_cpu_io_lsu_wmask)
  );
  MemBridge bridge (
    .clock                   (clock),
    .reset                   (reset),
    .io_ifu_addr             (_cpu_io_ifu_addr),
    .io_ifu_reqValid         (_cpu_io_ifu_reqValid),
    .io_ifu_rdata            (_bridge_io_ifu_rdata),
    .io_ifu_respValid        (_bridge_io_ifu_respValid),
    .io_lsu_addr             (_cpu_io_lsu_addr),
    .io_lsu_reqValid         (_cpu_io_lsu_reqValid),
    .io_lsu_rdata            (_bridge_io_lsu_rdata),
    .io_lsu_respValid        (_bridge_io_lsu_respValid),
    .io_lsu_size             (_cpu_io_lsu_size),
    .io_lsu_wen              (_cpu_io_lsu_wen),
    .io_lsu_wdata            (_cpu_io_lsu_wdata),
    .io_lsu_wmask            (_cpu_io_lsu_wmask),
    .io_master_awready      (io_master_awready),
    .io_master_awvalid      (io_master_awvalid),
    .io_master_awid    (io_master_awid),
    .io_master_awaddr  (io_master_awaddr),
    .io_master_awlen   (io_master_awlen),
    .io_master_awsize  (io_master_awsize),
    .io_master_awburst (io_master_awburst),
    .io_master_wready       (io_master_wready),
    .io_master_wvalid       (io_master_wvalid),
    .io_master_wdata   (io_master_wdata),
    .io_master_wstrb   (io_master_wstrb),
    .io_master_wlast   (io_master_wlast),
    .io_master_bready       (io_master_bready),
    .io_master_bvalid       (io_master_bvalid),
    .io_master_bid     (io_master_bid),
    .io_master_bresp   (io_master_bresp),
    .io_master_arready      (io_master_arready),
    .io_master_arvalid      (io_master_arvalid),
    .io_master_arid    (io_master_arid),
    .io_master_araddr  (io_master_araddr),
    .io_master_arlen   (io_master_arlen),
    .io_master_arsize  (io_master_arsize),
    .io_master_arburst (io_master_arburst),
    .io_master_rready       (io_master_rready),
    .io_master_rvalid       (io_master_rvalid),
    .io_master_rid     (io_master_rid),
    .io_master_rdata   (io_master_rdata),
    .io_master_rresp   (io_master_rresp),
    .io_master_rlast   (io_master_rlast)
  );
  assign io_slave_awready = 1'h0;
  assign io_slave_wready = 1'h0;
  assign io_slave_bvalid = 1'h0;
  assign io_slave_bid = 4'h0;
  assign io_slave_bresp = 2'h0;
  assign io_slave_arready = 1'h0;
  assign io_slave_rvalid = 1'h0;
  assign io_slave_rid = 4'h0;
  assign io_slave_rdata = 32'h0;
  assign io_slave_rresp = 2'h0;
  assign io_slave_rlast = 1'h0;
endmodule

module MemBridge(
  input         clock,
                reset,
  input  [31:0] io_ifu_addr,
  input         io_ifu_reqValid,
  output [31:0] io_ifu_rdata,
  output        io_ifu_respValid,
  input  [31:0] io_lsu_addr,
  input         io_lsu_reqValid,
  output [31:0] io_lsu_rdata,
  output        io_lsu_respValid,
  input  [1:0]  io_lsu_size,
  input         io_lsu_wen,
  input  [31:0] io_lsu_wdata,
  input  [3:0]  io_lsu_wmask,
  input         io_master_awready,
  output        io_master_awvalid,
  output [3:0]  io_master_awid,
  output [31:0] io_master_awaddr,
  output [7:0]  io_master_awlen,
  output [2:0]  io_master_awsize,
  output [1:0]  io_master_awburst,
  input         io_master_wready,
  output        io_master_wvalid,
  output [31:0] io_master_wdata,
  output [3:0]  io_master_wstrb,
  output        io_master_wlast,
                io_master_bready,
  input         io_master_bvalid,
  input  [3:0]  io_master_bid,
  input  [1:0]  io_master_bresp,
  input         io_master_arready,
  output        io_master_arvalid,
  output [3:0]  io_master_arid,
  output [31:0] io_master_araddr,
  output [7:0]  io_master_arlen,
  output [2:0]  io_master_arsize,
  output [1:0]  io_master_arburst,
  output        io_master_rready,
  input         io_master_rvalid,
  input  [3:0]  io_master_rid,
  input  [31:0] io_master_rdata,
  input  [1:0]  io_master_rresp,
  input         io_master_rlast
);

  wire        isValidLoad = io_lsu_reqValid & ~io_lsu_wen;
  wire        isValidStore = io_lsu_reqValid & io_lsu_wen;
  reg  [1:0]  stateI;
  wire        _io_master_arvalid_T = stateI == 2'h0;
  wire        _io_master_arvalid_T_2 = stateI == 2'h1;
  wire        _instReturn_T = stateI == 2'h2;
  reg  [2:0]  stateD;
  wire        _io_master_wvalid_T = stateD == 3'h0;
  wire        _lsuRead_T_2 = stateD == 3'h1;
  wire        _io_lsu_respValid_T = stateD == 3'h2;
  wire        _io_master_awvalid_T_2 = stateD == 3'h3;
  wire        _io_master_awvalid_T_3 = stateD == 3'h5;
  wire        _io_master_wvalid_T_2 = stateD == 3'h4;
  wire        io_master_bready_0 = stateD == 3'h6;
  wire        lsuRead = _io_master_wvalid_T & isValidLoad | _lsuRead_T_2;
  wire        instReturn = io_master_rvalid & _instReturn_T;
  reg  [31:0] io_ifu_rdata_r;
  always @(posedge clock) begin
    if (reset) begin
      stateI <= 2'h0;
      stateD <= 3'h0;
    end
    else begin
      automatic logic [1:0] _stateD_T_22 = io_master_arready ? 2'h2 : 2'h1;
      automatic logic [1:0] _stateD_T_24 = {~io_master_rvalid, 1'h0};
      automatic logic [2:0] _stateD_T_30 = {1'h1, io_master_wready, 1'h0};
      automatic logic [2:0] _stateD_T_21 =
        _io_master_wvalid_T
          ? (isValidLoad
               ? {1'h0, _stateD_T_22}
               : isValidStore
                   ? (io_master_awready ? _stateD_T_30 : io_master_wready ? 3'h5 : 3'h3)
                   : 3'h0)
          : 3'h0;
      stateI <=
        (_io_master_arvalid_T & io_ifu_reqValid | _io_master_arvalid_T_2
           ? _stateD_T_22
           : 2'h0) | (_instReturn_T ? _stateD_T_24 : 2'h0);
      stateD <=
        {_stateD_T_21[2],
         _stateD_T_21[1:0] | (_lsuRead_T_2 ? _stateD_T_22 : 2'h0)
           | (_io_lsu_respValid_T ? _stateD_T_24 : 2'h0)}
        | (_io_master_awvalid_T_2 ? (io_master_awready ? _stateD_T_30 : 3'h3) : 3'h0)
        | (_io_master_awvalid_T_3 ? (io_master_awready ? 3'h6 : 3'h5) : 3'h0)
        | (_io_master_wvalid_T_2 ? _stateD_T_30 : 3'h0)
        | (~io_master_bready_0 | io_master_bvalid ? 3'h0 : 3'h6);
    end
    if (instReturn)
      io_ifu_rdata_r <= io_master_rdata;
  end // always @(posedge)
  `ifdef ENABLE_INITIAL_REG_
    `ifdef FIRRTL_BEFORE_INITIAL
      `FIRRTL_BEFORE_INITIAL
    `endif // FIRRTL_BEFORE_INITIAL
    initial begin
      automatic logic [31:0] _RANDOM[0:1];
      `ifdef INIT_RANDOM_PROLOG_
        `INIT_RANDOM_PROLOG_
      `endif // INIT_RANDOM_PROLOG_
      `ifdef RANDOMIZE_REG_INIT
        for (logic [1:0] i = 2'h0; i < 2'h2; i += 2'h1) begin
          _RANDOM[i[0]] = `RANDOM;
        end
        stateI = _RANDOM[1'h0][1:0];
        stateD = _RANDOM[1'h0][4:2];
        io_ifu_rdata_r = {_RANDOM[1'h0][31:5], _RANDOM[1'h1][4:0]};
      `endif // RANDOMIZE_REG_INIT
    end // initial
    `ifdef FIRRTL_AFTER_INITIAL
      `FIRRTL_AFTER_INITIAL
    `endif // FIRRTL_AFTER_INITIAL
  `endif // ENABLE_INITIAL_REG_
  assign io_ifu_rdata = instReturn ? io_master_rdata : io_ifu_rdata_r;
  assign io_ifu_respValid = instReturn;
  assign io_lsu_rdata = io_master_rdata;
  assign io_lsu_respValid =
    _io_lsu_respValid_T & io_master_rvalid | io_master_bready_0 & io_master_bvalid;
  assign io_master_awvalid =
    |{_io_master_wvalid_T & isValidStore,
      _io_master_awvalid_T_3,
      _io_master_awvalid_T_2};
  assign io_master_awid = 4'h0;
  assign io_master_awaddr = io_lsu_addr;
  assign io_master_awlen = 8'h0;
  assign io_master_awsize = {1'h0, io_lsu_size};
  assign io_master_awburst = 2'h0;
  assign io_master_wvalid = _io_master_wvalid_T & isValidStore | _io_master_wvalid_T_2;
  assign io_master_wdata = io_lsu_wdata;
  assign io_master_wstrb = io_lsu_wmask;
  assign io_master_wlast = 1'h1;
  assign io_master_bready = io_master_bready_0;
  assign io_master_arvalid =
    _io_master_arvalid_T & io_ifu_reqValid | _io_master_arvalid_T_2 | lsuRead;
  assign io_master_arid = 4'h0;
  assign io_master_araddr = lsuRead ? io_lsu_addr : io_ifu_addr;
  assign io_master_arlen = 8'h0;
  assign io_master_arsize = {1'h0, lsuRead ? io_lsu_size : 2'h2};
  assign io_master_arburst = 2'h0;
  assign io_master_rready = _instReturn_T | _io_lsu_respValid_T;
endmodule
