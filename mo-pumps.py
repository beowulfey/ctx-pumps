import marimo

__generated_with = "0.6.11"
app = marimo.App()


@app.cell
def title(mo):
    mo.md(
        f"""
        ## Pump Program Builder
        Use this to design a series of concentrations while imaging.
        """
    )
    return


@app.cell
def __(logging, mo):
    # Export Run Log for tracking purposes

    log_loc = "./run_log.log"

    logging.basicConfig(filename=log_loc, encoding="utf-8", level=logging.INFO)

    get_csv_loc, set_csv_loc = mo.state(None)
    return get_csv_loc, log_loc, set_csv_loc


@app.cell
def pump_init(mo, nesp_lib):
    ###### SET PORT HERE
    _port = "/dev/cu.usbserial-210"

    banner = mo.md(
        f""" 
        # **<span style="color:red"> UNABLE TO CONNECT TO PUMPS** </span>
        """
    )

    # Initialize Pumps
    try:
        port = nesp_lib.Port(_port, 19200)
    except:
        port = None
    else:
        pump_a = nesp_lib.Pump(port, address=0)
        pump_b = nesp_lib.Pump(port, address=1)
        pumps = [pump_a, pump_b]

    banner if not port else None
    return banner, port, pump_a, pump_b, pumps


@app.cell
def __(mo):
    ### Initialize the application for your pump settings.

    form = (
        mo.md(
            """
        **Pump Parameters**

        Total flow rate: {flow} (ml/min)

        Pump A syringe concentration: {pac} (mM)

        Pump B syringe concentration: {pbc} (mM)

        ---
    """
        )
        .batch(
            flow=mo.ui.number(0, 9, 0.1, value=0.2),
            pac=mo.ui.number(0, 150, 5, value=0),
            pbc=mo.ui.number(0, 150, 5, value=150),
        )
        .form()
    )
    form
    return form,


@app.cell
def tab_builder(tabs):
    ### TAB LAYOUT CELL
    tabs
    return


@app.cell
def functions(
    Segment,
    datetime,
    form,
    get_curr_seg,
    get_pump_start,
    get_segs,
    get_total_time,
    logging,
    pd_converter,
    port,
    pump_a,
    pump_b,
    pumps,
    seg_conc_box,
    seg_len_box,
    set_csv_loc,
    set_curr_seg,
    set_pump_start,
    set_pump_time,
    set_seg_added,
    set_segs,
    set_total_time,
):
    ### SEGMENT BUILDER LOGIC AND UI


    def calculate_flowrates(conc_desired):
        """determines the flow rates for each pump based on the settings"""
        total_flow = float(form.value["flow"])
        conc_a = float(form.value["pac"])
        conc_b = float(form.value["pbc"])
        a_rate = ((conc_desired - conc_b) / (conc_a - conc_b)) * total_flow
        b_rate = total_flow - a_rate
        return [abs(a_rate), abs(b_rate)]


    def update_pumps(conc):
        concs = calculate_flowrates(conc)
        logging.info(f"{datetime.now()}: pumps updated to {concs} ml/min")
        if port:
            for n, pump in enumerate(pumps):
                pump.pumping_rate = float(concs[n])
                pump.pumping_direction = pd_converter("INFUSE")


    def start_pumps(conc):
        concs = calculate_flowrates(conc)
        logging.info(f" {datetime.now()}: RUNNING PUMPS AT {concs} ml/min")
        if port:
            #    set_flows(concs)
            if pump_a.running:
                pump_a.stop()
            if pump_b.running:
                pump_b.stop()
            for n, pump in enumerate(pumps):
                if float(concs[n]) > 0:
                    pump.pumping_rate = float(concs[n])
                    pump.run(wait_while_running=False)
            # pump_a.run(wait_while_running=False)
            # pump_b.run(wait_while_running=False)


    def stop_pumps():
        logging.info(f"{datetime.now()}: BOTH PUMPS STOPPED")
        if port:
            pump_a.stop()
            pump_b.stop()


    def add_seg():
        """add a segment to the list of segments state"""
        if seg_len_box.value > 0 and seg_conc_box.value >= 0:  # no adding blank segments
            set_segs(
                lambda v: v
                + [
                    Segment(
                        seg_len_box.value * 60,
                        seg_conc_box.value,
                    )
                ]
            )
            set_seg_added(True)


    def add_grad():
        """makes lots of tiny segments via add_seg()"""


    def rm_last_seg():
        """
        delete just the final segment from the state
        list (if you made an oopsie)
        """
        if len(get_segs()) > 0:
            set_segs(lambda s: s[:-1])


    def clear_segs():
        """delete all segments from the state"""
        set_segs([])


    def stop_protocol():
        logging.info(f" {datetime.now()}: PROTOCOL STOPPED")
        set_pump_start(None)
        set_pump_time(None)
        set_total_time(None)
        set_csv_loc(None)
        set_curr_seg(0)
        if port:
            pump_a.stop()
            pump_b.stop()


    def start_protocol():
        set_pump_start(datetime.now())
        # set_csv_loc(csv_loc + f"{get_pump_start().strftime('%Y-%m-%d_%H-%M')}" + ".csv")
        _pac = form.value["pac"]
        _pbc = form.value["pbc"]
        _flow = form.value["flow"]
        logging.info(f" ###############################################################")
        logging.info(f" PUMP STARTED: {get_pump_start()}")
        logging.info(f" Pump A is {_pac} mM, Pump B is {_pbc} mM")
        logging.info(f" Total flow rate is {_flow} ml/min")
        logging.info(f" PROTOCOL SETTINGS: (sec, conc) {[(x.time, x.conc) for x in get_segs()]} ")
        # logging.info(f" saving run to CSV at {get_csv_loc()}")
        # with open(get_csv_loc(), "wb", newline="") as f:
        #    writer = csv.writer(f)
        #    writer.writerow(["TIME", "CONC", "PUMP_A", "PUMP_B"])
        #    f.close()
        _time = 0.0
        if len(get_segs()) > 0:
            for seg in get_segs():
                _time = _time + seg.time
        set_total_time(_time)
        logging.info(f" {datetime.now()}: INITIATE: {get_pump_start()}, {get_total_time()}")
        start_pumps(get_segs()[get_curr_seg()].conc)
        advance_time()


    def advance_time():
        """
        This function tracks the current time relative to the length of the
        protocol, and is how it knows to switch to the next segment.
        """
        if get_pump_start() != None:
            _time = (datetime.now() - get_pump_start()).total_seconds()  # get time in protocol
            if _time < get_total_time():  # we haven't gone through the whole run
                set_pump_time(datetime.now())
                timer = get_segs()[0].time  # timer starts at the length of segment 1
                segi = 0

                while True:
                    if timer <= _time:
                        for n, seg in enumerate(get_segs()):
                            if n > 0:
                                segi = segi + 1
                                timer = timer + seg.time
                                if timer > _time:
                                    break
                        break
                    else:
                        # if timer > total time
                        break
                if segi > get_curr_seg():
                    set_curr_seg(segi)
                    logging.info(f" {datetime.now()}: Segment change! Now on segment {segi}, {get_curr_seg()}")
                    start_pumps(get_segs()[get_curr_seg()].conc)
                    # LOG!
                logging.info(f" {datetime.now()} SEG IS {segi}, TIMER IS {timer}, TIME IS {_time}")
                # with open(get_csv_loc(), "w") as f:
                #    _conc = get_segs()[get_curr_seg()].conc
                #    _concs = calculate_flowrates(_conc)
                #    writer = csv.writer(f)
                #    # writer.writerow('TIME', 'CONC', 'PUMP_A', 'PUMP_B')
                #    writer.writerow(
                #        f"{_time}", f"{_conc}", f"{_concs[0]}", f"{_concs[1]}"
                #    )
                #    f.close()
            else:
                stop_protocol()
    return (
        add_grad,
        add_seg,
        advance_time,
        calculate_flowrates,
        clear_segs,
        rm_last_seg,
        start_protocol,
        start_pumps,
        stop_protocol,
        stop_pumps,
        update_pumps,
    )


@app.cell
def __(advance_time, refresh):
    refresh
    advance_time()
    return


@app.cell
def __(
    add_seg_button,
    clear_segs_button,
    get_curr_seg,
    get_pump_start,
    get_pump_time,
    get_segs,
    get_total_time,
    mo,
    padir,
    paf,
    pbdir,
    pbf,
    rm_last_seg_button,
    seg_ax,
    seg_conc_box,
    seg_len_box,
    start_pa_button,
    start_pb_button,
    start_protocol_button,
    start_pump_button,
    stop_pa_button,
    stop_pb_button,
    stop_protocol_button,
    stop_pump_button,
    tab1_desired_conc_number,
    update_pump_button,
):
    ### TAB SET UP
    ### Strictly UI stuff here

    # SEGMENT TAB
    tab1 = mo.vstack(
        [
            mo.md("### Single Run"),
            mo.hstack(
                [
                    mo.md("Desired Concentration: "),
                    tab1_desired_conc_number,
                    mo.md(" (mM)"),
                ],
                justify="start",
            ),
            mo.hstack(
                [update_pump_button, start_pump_button, stop_pump_button],
                justify="start",
            ),
        ]
    )

    tab2 = mo.vstack(
        [
            mo.md("### Segment Builder"),
            seg_ax,
            mo.hstack(
                [mo.md("Segment length: "), seg_len_box, mo.md(" (min)")],
                justify="start",
            ),
            mo.hstack(
                [mo.md("Concentration: "), seg_conc_box, mo.md(" (mM)")],
                justify="start",
            ),
            mo.hstack(
                [add_seg_button, rm_last_seg_button, clear_segs_button],
                justify="start",
            ),
            mo.hstack([start_protocol_button, stop_protocol_button], justify="start"),
            (mo.md(f"Start Time is {get_pump_start()}") if get_pump_start() else None),
            (
                mo.md(f"Current Time is {((get_pump_time()-get_pump_start()).total_seconds()/60):.3f} min")
                if get_pump_start()
                else None
            ),
            (mo.md(f"Total Time is {(get_total_time()/60):.2f} min") if get_pump_start() else None),
            (mo.md(f"Current Concentration is {get_segs()[get_curr_seg()].conc}") if get_pump_start() else None),
        ]
    )

    tab3 = mo.vstack(
        [
            mo.md("### Utilities"),
            mo.hstack(
                [
                    mo.callout(
                        mo.vstack(
                            [
                                mo.md("**Pump A**"),
                                mo.hstack([mo.md("Flow: "), paf, mo.md("(ml/min)")]),
                                mo.hstack([mo.md("Direction: "), padir]),
                                mo.hstack(
                                    [start_pa_button, stop_pa_button],
                                    justify="start",
                                ),
                            ]
                        )
                    ),
                    mo.callout(
                        mo.vstack(
                            [
                                mo.md("**Pump B**"),
                                mo.hstack([mo.md("Flow: "), pbf, mo.md("(ml/min)")]),
                                mo.hstack([mo.md("Direction: "), pbdir]),
                                mo.hstack(
                                    [start_pb_button, stop_pb_button],
                                    justify="start",
                                ),
                            ]
                        )
                    ),
                ],
                justify="center",
            ),
        ]
    )

    tabs = mo.tabs(
        {
            "Dumb Control": tab1,
            "Protocol Builder": tab2,
            "Utilities": tab3,
        }
    )
    return tab1, tab2, tab3, tabs


@app.cell
def classes(dataclass):
    ### CLASSES
    @dataclass
    class Segment:
        """
        A protocol segment is essentially just a concentration
        and a length of time, which I've set to seconds.
        """

        time: float  # seconds
        conc: int  # millimolar
    return Segment,


@app.cell
def states(mo):
    ### STATES

    # Segment Builder States
    get_segs, set_segs = mo.state([])
    seg_added, set_seg_added = mo.state(False)

    # Pumps
    pump_confirmed, set_pump_confirmed = mo.state(False)
    get_pump_start, set_pump_start = mo.state(None)
    get_pump_time, set_pump_time = mo.state(None)
    get_total_time, set_total_time = mo.state(None)
    get_curr_seg, set_curr_seg = mo.state(0)
    return (
        get_curr_seg,
        get_pump_start,
        get_pump_time,
        get_segs,
        get_total_time,
        pump_confirmed,
        seg_added,
        set_curr_seg,
        set_pump_confirmed,
        set_pump_start,
        set_pump_time,
        set_seg_added,
        set_segs,
        set_total_time,
    )


@app.cell
def ui_elements(
    add_seg,
    clear_segs,
    mo,
    rm_last_seg,
    start_protocol,
    start_pumps,
    stop_protocol,
    stop_pumps,
    tab1_desired_conc_number,
    update_pumps,
):
    ### UI ELEMENTS
    #   All buttons, spots, etc.

    add_seg_button = mo.ui.button(label="add segment", on_change=lambda _: add_seg())

    rm_last_seg_button = mo.ui.button(label="remove last segment", on_change=lambda _: rm_last_seg())

    clear_segs_button = mo.ui.button(label="clear all segments", on_change=lambda _: clear_segs())

    start_protocol_button = mo.ui.button(label="Start Run", kind="success", on_change=lambda _: start_protocol())

    stop_protocol_button = mo.ui.button(label="Stop Run", kind="danger", on_change=lambda _: stop_protocol())

    update_pump_button = mo.ui.button(
        label="Update settings",
        on_change=lambda _: update_pumps(tab1_desired_conc_number.value),
    )

    start_pump_button = mo.ui.button(
        label="Start Pump",
        kind="success",
        on_change=lambda _: start_pumps(tab1_desired_conc_number.value),
    )

    stop_pump_button = mo.ui.button(label="Stop Pump", kind="danger", on_change=lambda _: stop_pumps())
    return (
        add_seg_button,
        clear_segs_button,
        rm_last_seg_button,
        start_protocol_button,
        start_pump_button,
        stop_protocol_button,
        stop_pump_button,
        update_pump_button,
    )


@app.cell
def seg_refresher(mo, seg_added):
    ### REFRESH SEGMENT UI COMPONENTS
    #   Since these are being refreshed when a segment is added, they
    #   can't be located in the main UI cell.
    seg_added

    seg_len_box = mo.ui.number(0, 10, step=0.25, value=0)
    seg_conc_box = mo.ui.number(0, 100, step=5, value=0)

    tab1_desired_conc_number = mo.ui.number(0, 100, 5, value=50)
    return seg_conc_box, seg_len_box, tab1_desired_conc_number


@app.cell
def __(mo, nesp_lib, port, pump_a, pump_b):
    # UTILITY CONTROL FUNCTIONS


    def pd_converter(direction):
        if port:
            if direction == "INFUSE":
                return nesp_lib.PumpingDirection.INFUSE
            elif direction == "WITHDRAW":
                return nesp_lib.PumpingDirection.WITHDRAW
            else:
                return None


    def start_pa():
        if port:
            if pump_a.running:
                pump_a.stop()
            """Pump A Utility Controller"""
            dir = pd_converter(padir.value)
            pump_a.pumping_direction = dir
            pump_a.pumping_rate = paf.value
            pump_a.run(wait_while_running=False)


    def stop_pa():
        if port:
            pump_a.stop()


    def start_pb():
        if port:
            """Pump B Utility Controller"""
            dir = pd_converter(pbdir.value)
            pump_b.pumping_direction = dir
            pump_b.pumping_rate = pbf.value
            pump_b.run(wait_while_running=False)


    def stop_pb():
        if port:
            pump_b.stop()


    paf = mo.ui.number(0, 14.5, 0.1, value=1)  # get_flows()[0])
    pbf = mo.ui.number(0, 14.5, 0.1, value=1)  # get_flows()[1])
    padir = mo.ui.dropdown(["INFUSE", "WITHDRAW"], value="INFUSE")
    pbdir = mo.ui.dropdown(["INFUSE", "WITHDRAW"], value="INFUSE")

    start_pa_button = mo.ui.button(label="Start", kind="success", on_change=lambda _: start_pa())
    stop_pa_button = mo.ui.button(label="Stop", kind="danger", on_change=lambda _: stop_pa())

    start_pb_button = mo.ui.button(label="Start", kind="success", on_change=lambda _: start_pb())
    stop_pb_button = mo.ui.button(label="Stop", kind="danger", on_change=lambda _: stop_pb())
    return (
        padir,
        paf,
        pbdir,
        pbf,
        pd_converter,
        start_pa,
        start_pa_button,
        start_pb,
        start_pb_button,
        stop_pa,
        stop_pa_button,
        stop_pb,
        stop_pb_button,
    )


@app.cell
def __(mo):
    # This outputs a timer that fires once a second

    refresh = mo.ui.refresh(default_interval="1s")
    refresh
    return refresh,


@app.cell
def __():
    ### NOTES AND SHIT
    #
    #   I EMPIRICALLY MEASURED THE FLOW RATE DUE TO GRAVITY IN MY SYSTEM
    #   Really just an approximate start point more than anything!
    #   Used 30 mL syringes, held at about 60-80 mm above the sample
    #   Tubing length used was 60.5 mm long, and the inner diameter is 0.51 mm
    #   Timing flow to end was about 8-8.25 seconds. So ~0.00745 m/s flow velocity
    #   Based on the diameter, this means a flow rate of about 0.15 ml/min
    #   Alternatively, 10.7 ml/hr, or 10700 uL/hr.
    #
    #   I've played around with flow rates, and a rate of ~0.4-0.5 ml/min is a good
    #   compromise between speed of flow (decreases time between switching) and
    #   backpressure.
    return


@app.cell
def imports():
    import marimo as mo
    import numpy as np
    from datetime import datetime
    import time
    import matplotlib.pyplot as plt
    from serial.tools import list_ports
    import nesp_lib
    from dataclasses import dataclass
    import logging
    import csv
    return (
        csv,
        dataclass,
        datetime,
        list_ports,
        logging,
        mo,
        nesp_lib,
        np,
        plt,
        time,
    )


@app.cell(disabled=True)
def __(form, stop_protocol_button):
    ## EMERGENCY STOP BUTTON (in case the form breaks)

    # dirbut = mo.ui.button(
    #    label="SET LOG LOCATION", kind="info", on_change=lambda _: select_log_dir()
    # )
    stop_protocol_button if form.value else None
    return


@app.cell
def seg_plotter(
    form,
    get_pump_start,
    get_pump_time,
    get_segs,
    plt,
    refresh,
):
    ### PLOTTING CELL
    #   This cell builds the plot used for the segment builder.
    #   It refreshes based on the refresh rate chosen.

    refresh

    _concs = []
    _times = []
    _count = 0

    for _s in get_segs():
        _times.append(_count)
        _concs.append(_s.conc)
        _count = _count + _s.time
        _times.append(_count)
        _concs.append(_s.conc)

    _f, seg_ax = plt.subplots(figsize=(8, 2))
    seg_ax.plot(
        [time / 60 for time in _times],
        _concs,
    )
    if get_pump_time() and get_pump_start():
        plt.axvline((get_pump_time() - get_pump_start()).total_seconds() / 60)


    seg_ax.set_ylabel("Conc (mM)")
    seg_ax.set_xlabel("Time (min)")
    if form.value:
        seg_ax.set_ylim([form.value["pac"], form.value["pbc"] * 1.10])
    _f.tight_layout()
    return seg_ax,


if __name__ == "__main__":
    app.run()
