import marimo

__generated_with = "0.1.77"
app = marimo.App()


@app.cell
def title(mo):
    ### NOTES AND SHIT
    #
    #   I EMPIRICALLY MEASURED THE FLOW RATE DUE TO GRAVITY IN MY SYSTEM
    #   Really just an approximate start point more than anything!
    #   Used 30 mL syringes, held at about 60-80 mm above the sample
    #   Tubing length used was 60.5 mm long, and the inner diameter is 0.51 mm
    #   Timing flow to end was about 8-8.25 seconds. So ~0.00745 m/s flow velocity
    #   Based on the diameter, this means a flow rate of about 0.15 ml/min
    #   Alternatively, 10.7 ml/hr, or 10700 uL/hr.

    mo.md(
        f"""
        ## Pump Program Builder
        Use this to design a series of concentrations while imaging. 
        """
    )
    return


@app.cell
def pump_init(nesp_lib):
    # Initialize Pumps

    port = nesp_lib.Port("/dev/cu.usbserial-2140", 19200)
    pump_a = nesp_lib.Pump(port, address=0)
    pump_b = nesp_lib.Pump(port, address=1)
    pumps = [pump_a, pump_b]
    return port, pump_a, pump_b, pumps


@app.cell
def __(mo):
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
            flow=mo.ui.number(0, 9, 0.1, value=0.167),
            pac=mo.ui.number(0, 100, 5, value=0),
            pbc=mo.ui.number(0, 100, 5, value=100),
        )
        .form()
    )
    form
    return form,


@app.cell
def tab_builder(mo, tab1, tab2, tab3):
    tabs = mo.tabs(
        {
            "Dumb Control": tab1,
            "Protocol Builder": tab2,
            "Utilities": tab3,
        }
    )
    tabs
    return tabs,


@app.cell
def tab_definer(
    add_seg_button,
    clear_segs_button,
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
    start_pump_button,
    stop_pa_button,
    stop_pb_button,
    stop_pump_button,
    tab1_desired_conc_number,
    update_pump_button,
):
    ### ASSEMBLE THE TABS
    tab3 = mo.vstack(
        [
            mo.md("### Utilities"),
            mo.hstack(
                [
                    mo.callout(
                        mo.vstack(
                            [
                                mo.md("**Pump A**"),
                                mo.hstack(
                                    [mo.md("Flow: "), paf, mo.md("(ml/min)")]
                                ),
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
                                mo.hstack(
                                    [mo.md("Flow: "), pbf, mo.md("(ml/min)")]
                                ),
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
        ]
    )
    return tab1, tab2, tab3


@app.cell
def __(mo, nesp_lib, pump_a, pump_b):
    def pd_converter(direction):
        if direction == "INFUSE":
            return nesp_lib.PumpingDirection.INFUSE
        elif direction == "WITHDRAW":
            return nesp_lib.PumpingDirection.WITHDRAW
        else:
            return None


    def start_pa():
        if pump_a.running:
            pump_a.stop()
        """Pump A Utility Controller"""
        dir = pd_converter(padir.value)
        pump_a.pumping_direction = dir
        pump_a.pumping_rate = paf.value
        pump_a.run(wait_while_running=False)


    def stop_pa():
        pump_a.stop()


    def start_pb():
        """Pump B Utility Controller"""
        dir = pd_converter(pbdir.value)
        pump_b.pumping_direction = dir
        pump_b.pumping_rate = pbf.value
        pump_b.run(wait_while_running=False)


    def stop_pb():
        pump_b.stop()


    paf = mo.ui.number(0, 14.5, 0.1, value=1)  # get_flows()[0])
    pbf = mo.ui.number(0, 14.5, 0.1, value=1)  # get_flows()[1])
    padir = mo.ui.dropdown(["INFUSE", "WITHDRAW"], value="INFUSE")
    pbdir = mo.ui.dropdown(["INFUSE", "WITHDRAW"], value="INFUSE")

    start_pa_button = mo.ui.button(
        label="Start", kind="success", on_change=lambda _: start_pa()
    )
    stop_pa_button = mo.ui.button(
        label="Stop", kind="danger", on_change=lambda _: stop_pa()
    )

    start_pb_button = mo.ui.button(
        label="Start", kind="success", on_change=lambda _: start_pb()
    )
    stop_pb_button = mo.ui.button(
        label="Stop", kind="danger", on_change=lambda _: stop_pb()
    )
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
def __(
    form,
    mo,
    pd_converter,
    pump_a,
    pump_b,
    pumps,
    tab1_desired_conc_number,
):
    # get_flows, set_flows = mo.state([1, 1])


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
        for n, pump in enumerate(pumps):
            pump.pumping_rate = float(concs[n])
            pump.pumping_direction = pd_converter("INFUSE")


    def start_pumps(conc):
        concs = calculate_flowrates(conc)
        #    set_flows(concs)
        if pump_a.running:
            pump_a.stop()
        if pump_b.running:
            pump_b.stop()
        for n, pump in enumerate(pumps):
            pump.pumping_rate = float(concs[n])

        pump_a.run(wait_while_running=False)
        pump_b.run(wait_while_running=False)


    def stop_pumps():
        pump_a.stop()
        pump_b.stop()


    update_pump_button = mo.ui.button(
        label="Update settings",
        on_change=lambda _: update_pumps(tab1_desired_conc_number.value),
    )

    start_pump_button = mo.ui.button(
        label="Start Pump",
        kind="success",
        on_change=lambda _: start_pumps(tab1_desired_conc_number.value),
    )

    stop_pump_button = mo.ui.button(
        label="Stop Pump", kind="danger", on_change=lambda _: stop_pumps()
    )
    return (
        calculate_flowrates,
        start_pump_button,
        start_pumps,
        stop_pump_button,
        stop_pumps,
        update_pump_button,
        update_pumps,
    )


@app.cell
def seg_refresher(mo, seg_added):
    # Refresh the entry form whenever a task is added
    # I guess this needs to be its own cell?
    seg_added

    seg_len_box = mo.ui.number(0, 10, step=0.25, value=0)
    seg_conc_box = mo.ui.number(0, 100, step=5, value=0)

    tab1_desired_conc_number = mo.ui.number(0, 100, 5, value=50)
    return seg_conc_box, seg_len_box, tab1_desired_conc_number


@app.cell
def classes_states(dataclass, mo):
    ### CLASSES FOR THINGS
    @dataclass
    class Segment:
        time: float  # minutes
        conc: int  # millimolar
        flows: list  # pump_a, pump_b


    ### STATES FOR THINGS

    # Segment Builder States
    get_segs, set_segs = mo.state([])
    seg_added, set_seg_added = mo.state(False)

    # Pumps
    # get_pumps, set_pumps = mo.state({})
    pump_confirmed, set_pump_confirmed = mo.state(False)
    pump_running, set_pump_running = mo.state(False)
    return (
        Segment,
        get_segs,
        pump_confirmed,
        pump_running,
        seg_added,
        set_pump_confirmed,
        set_pump_running,
        set_seg_added,
        set_segs,
    )


@app.cell
def functions(
    Segment,
    get_segs,
    mo,
    seg_conc_box,
    seg_len_box,
    set_seg_added,
    set_segs,
):
    ### THESE ARE FOR THE LOGIC OF THE SEGMENT BUILDER UI


    def add_seg():
        """add a segment to the list of segments state"""
        if (
            seg_len_box.value > 0 and seg_conc_box.value > 0
        ):  # no adding blank segments
            set_segs(
                lambda v: v
                + [
                    Segment(
                        seg_len_box.value,
                        seg_conc_box.value,
                        # calculate_flowrates(
                        #    get_pumps()[0].
                        #    select_pumpB_conc.value,
                        #    seg_conc_box.value,
                        #    select_flow_rate.value,
                        # ),
                    )
                ]
            )
            set_seg_added(True)


    def rm_last_seg():
        """delete just the final segment from the state list (if you made an oopsie)"""
        if len(get_segs()) > 0:
            set_segs(lambda s: s[:-1])


    def clear_segs():
        """delete all segments from the state"""
        set_segs([])


    add_seg_button = mo.ui.button(
        label="add segment", on_change=lambda _: add_seg()
    )

    rm_last_seg_button = mo.ui.button(
        label="remove last segment", on_change=lambda _: rm_last_seg()
    )

    clear_segs_button = mo.ui.button(
        label="clear all segments", on_change=lambda _: clear_segs()
    )
    return (
        add_seg,
        add_seg_button,
        clear_segs,
        clear_segs_button,
        rm_last_seg,
        rm_last_seg_button,
    )


@app.cell
def imports():
    import marimo as mo
    import numpy as np
    import matplotlib.pyplot as plt
    from serial.tools import list_ports
    import nesp_lib
    from dataclasses import dataclass
    return dataclass, list_ports, mo, nesp_lib, np, plt


@app.cell
def seg_plotter(form, get_segs, plt):
    ### PLOTTING CELL
    #   This cell builds the plot used for the segment builder
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
        _times,
        _concs,
    )
    seg_ax.set_ylabel("Conc (mM)")
    seg_ax.set_xlabel("Time (min)")
    if form.value:
        seg_ax.set_ylim([form.value["pac"], form.value["pbc"] * 1.10])
    _f.tight_layout()
    return seg_ax,


if __name__ == "__main__":
    app.run()
