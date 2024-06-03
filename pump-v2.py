import marimo

__generated_with = "0.6.13"
app = marimo.App()


@app.cell
def __(logging, mo, nesp_lib, port_dropdown):
    ### This cell shows a banner if the pumps are not properly connected.

    _banner = mo.md(
        f""" 
        # **<span style="color:red"> UNABLE TO CONNECT TO PUMPS** </span>
        """
    )

    # Initialize Pumps.
    # The global "port" variable allows for logic to work with or without a pump connected, # for testing purposes.
    try:
        port = nesp_lib.Port(port_dropdown.value, 19200)
    except:
        port = None
    else:
        _pump_a = nesp_lib.Pump(port, address=0)
        _pump_b = nesp_lib.Pump(port, address=1)
        pumps = [_pump_a, _pump_b]

    if not port:
        logging.info("@@@@@ Unable to connect to pump! Operating in test mode")

    _banner if not port else None
    return port, pumps


@app.cell(hide_code=True)
def __(mo):
    mo.md(
        f"""
        ## Pump Program Builder
        Use this to design a series of concentrations while imaging.
        """
    )
    return


@app.cell
def __(datetime, logging, mo, ports):
    ### Contains a form that sets the pump parameters


    def _submit_form():
        # Logs when the form is submitted.
        logging.warning(
            f"\n#################################################\n {datetime.now()}: FORM SUBMITTED WITH DATA\n{form.value}\n#################################################"
        )


    form = (
        mo.md(
            """
        **Pump Parameters**

        Pump Port: {port_select}

        Total flow rate: {flow} (ml/min)

        Pump A syringe concentration: {pac} (mM)

        Pump B syringe concentration: {pbc} (mM)

        Pump update rate: every {pur} (sec)

        ---
    """
        )
        .batch(
            port_select=mo.ui.dropdown(ports, value=ports[0]),
            flow=mo.ui.number(0, 9, 0.1, value=0.4),
            pac=mo.ui.number(0, 150, 5, value=0),
            pbc=mo.ui.number(0, 150, 5, value=100),
            pur=mo.ui.slider(0.1, 1, 0.1, value=0.5),
        )
        .form(on_change=lambda _: _submit_form())
    )
    form
    return form,


@app.cell(hide_code=True)
def __(
    add_seg_button,
    clear_segs_button,
    form,
    grad_conc_box,
    leave_pump_running,
    mo,
    rm_last_seg_button,
    run_pumps_button,
    seg_ax,
    seg_conc_box,
    seg_len_box,
    start_protocol_button,
    stop_protocol_button,
    stop_pumps_button,
    straight_run_conc,
    update_pumps_button,
):
    ### Contains tab layouts for the main app.

    _run_tab = mo.vstack(
        [
            mo.md("### Basic Pump Control"),
            mo.hstack(
                [
                    mo.md("Desired Concentration: "),
                    straight_run_conc,
                    mo.md(" (mM)"),
                ],
                justify="start",
            ),
            mo.hstack(
                [run_pumps_button, update_pumps_button, stop_pumps_button],
                justify="start",
            ),
        ]
    )

    _seg_tab = mo.vstack(
        [
            mo.hstack(
                [mo.md("Segment length: "), seg_len_box, mo.md(" (min)")],
                justify="start",
            ),
            mo.hstack(
                [mo.md("Concentration: "), seg_conc_box, mo.md(" (mM)")],
                justify="start",
            ),
            mo.hstack(
                [mo.md("End Conc: "), grad_conc_box, mo.md(" (mM)")],
                justify="start",
            ),
            mo.hstack(
                [add_seg_button, rm_last_seg_button, clear_segs_button,],
                justify="start",
            ),
        ]
    )


    _protocol = mo.vstack(
        [
            mo.md("### Protocol Builder"),
            seg_ax,
            _seg_tab,
            mo.hstack([start_protocol_button, stop_protocol_button, mo.md("Leave pump running: "), leave_pump_running], justify="start"),
        ]
    )

    _tabs = mo.ui.tabs(
        {
            "Dumb Control": _run_tab,
            "Protocol Builder": _protocol,
        }
    )

    _tabs if form.value else None
    return


@app.cell
def __(
    add_seg,
    clear_segs,
    form,
    mo,
    rm_seg,
    run_pumps,
    set_pump_start,
    start_protocol,
    stop_pumps,
    update_pumps,
):
    ### Global UI Components that must be accessed here.

    # Get pump concentration parameters.
    _pac = int(form.value["pac"]) if form.value is not None else 0
    _pbc = int(form.value["pbc"]) if form.value is not None else 100

    # For straight runs, doesn't let you go higher or lower than pump values.
    straight_run_conc = mo.ui.number(_pac, _pbc, 5, value=(_pac + _pbc) / 2)



    # Update
    update_pumps_button = mo.ui.button(
        label="Update Pumps",
        on_change=lambda _: update_pumps(straight_run_conc.value),
    )

    run_pumps_button = mo.ui.button(
        label="Run Pumps",
        kind="success",
        on_change=lambda _: run_pumps(straight_run_conc.value),
    )

    stop_pumps_button = mo.ui.button(label="Stop Pumps", kind="danger", on_change=lambda _: stop_pumps())

    add_seg_button = mo.ui.button(label="add segment", on_change=lambda _: add_seg())

    rm_last_seg_button = mo.ui.button(label="remove last segment", on_change=lambda _: rm_seg())

    clear_segs_button = mo.ui.button(label="clear all segments", on_change=lambda _: clear_segs())

    start_protocol_button = mo.ui.button(label="Start Run", kind="success", on_change=lambda _: start_protocol())

    stop_protocol_button = mo.ui.button(label="Stop Run", kind="danger", on_change=lambda _: set_pump_start(False))#_: stop_protocol(True))
    return (
        add_seg_button,
        clear_segs_button,
        rm_last_seg_button,
        run_pumps_button,
        start_protocol_button,
        stop_protocol_button,
        stop_pumps_button,
        straight_run_conc,
        update_pumps_button,
    )


@app.cell
def __(form, mo, seg_added):
    # Sets default values for concentration selector
    _pac = int(form.value["pac"]) if form.value is not None else 0
    _pbc = int(form.value["pbc"]) if form.value is not None else 100
    seg_added
    seg_len_box = mo.ui.number(0, 120, step=0.1, value=0)
    seg_conc_box = mo.ui.number(_pac, _pbc, step=5, value=0)
    return seg_conc_box, seg_len_box


@app.cell(hide_code=True)
def __(form, mo, seg_added, seg_conc_box):
    # Sets default values for gradient concentration selector
    _pac = int(form.value["pac"]) if form.value is not None else 0
    _pbc = int(form.value["pbc"]) if form.value is not None else 100
    seg_added
    grad_conc_box = mo.ui.number(_pac, _pbc, step=5, value=seg_conc_box.value)
    return grad_conc_box,


@app.cell
def __(
    Segment,
    datetime,
    form,
    get_curr,
    get_prot,
    get_pump_start,
    get_segs,
    grad_conc_box,
    logging,
    mo,
    nesp_lib,
    np,
    port,
    pumps,
    seg_conc_box,
    seg_len_box,
    set_curr,
    set_prot,
    set_pump_start,
    set_running,
    set_seg_added,
    set_segs,
    time,
):
    ### Functions and utilities.

    # UTILITIES


    def calculate_flowrates(_conc):
        # Determines the flow rates for each pump based on the pump settings.
        _conc = float(_conc)
        _pac = float(form.value["pac"])
        _pbc = float(form.value["pbc"])
        _flow = float(form.value["flow"])
        # Flow rates are basically a proportion based on total flow and concs
        _b_rate = ((_conc - _pac) / (_pbc - _pac)) * _flow
        _a_rate = _flow - _b_rate
        # returns the flow rates rounded to three decimal places.
        return [round(abs(_a_rate), 3), round(abs(_b_rate), 3)]


    def generate_timepoints():
        xtot = []
        ytot = []
        total_time = 0
        for seg in get_segs():
            x = [total_time, total_time + seg.time]
            y = [seg.conc_in, seg.conc_out]
            print(x, y)
            steps = int(seg.time / form.value["pur"]) + 1
            x_expanded = np.linspace(x[0], x[1], steps, endpoint=True)
            y_expanded = np.interp(x_expanded, x, y)
            print(x_expanded, y_expanded)
            xtot = xtot + x_expanded.tolist()
            ytot = ytot + y_expanded.tolist()
            total_time += seg.time
        return [xtot, ytot]


    # PUMP CONTROL


    def run_pumps(_conc):
        # Runs the pumps at a specific flowrate.
        _concs = calculate_flowrates(_conc)
        logging.info(f" {datetime.now()}: RUNNING PUMPS AT {_concs} ml/min")
        # First, checks if pumps are running and stops them if so.
        if port:
            for _pump in pumps:
                if _pump.running:
                    _pump.stop()
            # Then, it runs the pumps at the new flow rates.
            for _n, _pump in enumerate(pumps):
                if float(_concs[_n]) > 0:
                    _pump.pumping_rate = float(_concs[_n])
                    _pump.run(wait_while_running=False)


    def stop_pumps():
        # Stops both pumps.
        logging.info(f"{datetime.now()}: BOTH PUMPS STOPPED")
        if port:
            for _pump in pumps:
                _pump.stop()


    def update_pumps(_conc):
        # Updates the pumps to the match the desired concentration.
        # Used to manually update the flow rate on the straight run tab.
        _concs = calculate_flowrates(_conc)
        logging.info(f"{datetime.now()}: pumps updated to {_concs} ml/min")
        if port:
            for _n, _pump in enumerate(pumps):
                _pump.pumping_direction = nesp_lib.PumpingDirection.INFUSE
                _pump.pumping_rate = float(_concs[_n])


    # SEGMENT FUNCTIONS


    def add_seg():
        # Adds a segment to the protocol.
        # Don't allow blank segments (of length 0 min)
        if seg_len_box.value > 0:
            _seg = [Segment(seg_len_box.value * 60, seg_conc_box.value, grad_conc_box.value)]
            set_segs(lambda v: v + _seg)
            # Refreshes the boxes
            set_seg_added(True)
            set_prot([[], []])
            set_prot(generate_timepoints())


    def rm_seg():
        # Removes the last segment from the protocol
        if len(get_segs()) > 0:
            set_segs(lambda s: s[:-1])


    def clear_segs():
        # Delete all segments from the protocol.
        set_segs([])
        set_prot([[], []])

    leave_pump_running = mo.ui.checkbox(value=True)

    def stop_protocol(force=False):
        set_pump_start(False)
        logging.info(f" {datetime.now()}: PROTOCOL STOPPED")
        if not force:
            stop_pumps() if leave_pump_running.value else None


    def start_protocol():
        #print("HELLO!")
        set_pump_start(True)
        _pac = form.value["pac"]
        _pbc = form.value["pbc"]
        _flow = form.value["flow"]
        logging.info(f" PROTOCOL SETTINGS: (seconds, conc_in, conc_out)  ")
        logging.info(f" {datetime.now()} <-- INITIATED AT THIS TIME")
        set_curr(0)
        run_protocol()

    def run_protocol():
        if get_pump_start():
            x,y = get_prot()
            if y:
                while get_curr() < len(y):
                    n = get_curr()
                    #print(y[n])
                    run_pumps(y[n])
                    time.sleep(form.value["pur"])
                    set_curr(get_curr()+1)
                    set_running(True)
            if get_curr() >= len(y):
                stop_protocol()
    return (
        add_seg,
        calculate_flowrates,
        clear_segs,
        generate_timepoints,
        leave_pump_running,
        rm_seg,
        run_protocol,
        run_pumps,
        start_protocol,
        stop_protocol,
        stop_pumps,
        update_pumps,
    )


@app.cell
def __(get_pump_start, run_protocol, running):
    running

    if get_pump_start():
        run_protocol()
    return


@app.cell
def __(mo):
    ### Global state variables

    # Segment Builder States
    get_segs, set_segs = mo.state([])
    seg_added, set_seg_added = mo.state(False)
    get_prot, set_prot = mo.state([[], []])
    get_pump_start, set_pump_start = mo.state(False)
    running, set_running = mo.state(False)
    get_curr, set_curr = mo.state(0)
    return (
        get_curr,
        get_prot,
        get_pump_start,
        get_segs,
        running,
        seg_added,
        set_curr,
        set_prot,
        set_pump_start,
        set_running,
        set_seg_added,
        set_segs,
    )


@app.cell
def __():
    ### Classes for functions


    class Segment:
        """
        A protocol segment is essentially just a concentration
        and a length of time, which I've set to seconds.
        """

        def __init__(self, _time, _conc_in, _conc_out):
            # time is seconds, concentration is millimolar
            self.time = _time
            self.conc_in = _conc_in
            self.conc_out = _conc_out
    return Segment,


@app.cell
def __(form, get_curr, get_prot, get_pump_start, plt):
    ### PLOTTING CELL
    #   This cell builds the plot used for the segment builder.
    #   It refreshes based on the refresh rate chosen.

    _times = get_prot()[0]
    _concs = get_prot()[1]
    _f, seg_ax = plt.subplots(figsize=(8, 2))
    seg_ax.plot(
        [time / 60.0 for time in _times],
        _concs,
    )

    if get_pump_start():
        print(get_prot()[0][get_curr()])
        plt.axvline((get_prot()[0][get_curr()])/60)
    seg_ax.set_ylabel("Conc (mM)")
    seg_ax.set_xlabel("Time (min)")
    if form.value:
        seg_ax.set_ylim([form.value["pac"], form.value["pbc"] * 1.10])
    _f.tight_layout()
    return seg_ax,


@app.cell
def __():
    import marimo as mo
    import numpy as np
    from datetime import datetime
    import time
    import matplotlib.pyplot as plt
    from serial.tools import list_ports
    import nesp_lib
    import logging
    from decimal import Decimal
    import asyncio

    ### Contains variables for logging and ports.

    # Logging Setup
    _today = datetime.strftime(datetime.now(), "%Y-%m-%d")
    logging.basicConfig(filename=f"./logs/{_today}_run.log", encoding="utf-8", level=logging.INFO)

    # Get COM ports for system.
    ports = [str(_port).split(" ")[0] for _port in list_ports.comports()]
    return (
        Decimal,
        asyncio,
        datetime,
        list_ports,
        logging,
        mo,
        nesp_lib,
        np,
        plt,
        ports,
        time,
    )


if __name__ == "__main__":
    app.run()
