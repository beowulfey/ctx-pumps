import marimo

__generated_with = "0.1.77"
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
def tab_builder(mo, tab1, tab2):
    tabs = mo.tabs({"Pump Settings": tab1, "Segment Builder": tab2})
    tabs
    return tabs,


@app.cell
def seg_plotter(get_segs, plt, select_pumpA_conc, select_pumpB_conc):
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
    seg_ax.set_ylim([select_pumpA_conc.value, select_pumpB_conc.value * 1.10])
    _f.tight_layout()
    return seg_ax,


@app.cell
def seg_refresher(mo, seg_added):
    # Refresh the entry form whenever a task is added
    # I guess this needs to be its own cell?
    seg_added

    seg_len_box = mo.ui.number(0, 10, step=0.25, value=0)
    seg_conc_box = mo.ui.number(0, 100, step=5, value=0)
    return seg_conc_box, seg_len_box


@app.cell
def tab_definer(
    add_seg_button,
    clear_segs_button,
    confirm_parameters_button,
    mo,
    rm_last_seg_button,
    seg_ax,
    seg_conc_box,
    seg_len_box,
    select_flow_rate,
    select_port,
    select_pumpA_conc,
    select_pumpB_conc,
    select_pump_syringe,
    syringe_lookup,
):
    ### ASSEMBLE THE TABS
    tab1 = mo.callout(
        mo.vstack(
            [
                mo.md("**Pump Parameters**"),
                mo.hstack(
                    [mo.md("TTY port: "), select_port],
                    justify="start",
                ),
                mo.hstack(
                    [
                        mo.md("Total Flow Rate: "),
                        select_flow_rate,
                        mo.md(" (ml/hr)"),
                    ],
                    justify="start",
                ),
                mo.hstack(
                    [
                        mo.md("Select syringe size: "),
                        select_pump_syringe,
                        mo.md(
                            f" (ID: {syringe_lookup(select_pump_syringe.value).in_dia} mm)"
                        ),
                    ],
                    justify="start",
                ),
                mo.hstack(
                    [
                        mo.md("Pump A Concentration: "),
                        select_pumpA_conc,
                        mo.md(" (mM)"),
                    ],
                    justify="start",
                ),
                mo.hstack(
                    [
                        mo.md("Pump B Concentration: "),
                        select_pumpB_conc,
                        mo.md(" (mM)"),
                    ],
                    justify="start",
                ),
                mo.hstack(
                    [confirm_parameters_button],
                    justify="end",
                ),
            ]
        ),
        kind="neutral",
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
    return tab1, tab2


@app.cell
def classes_states(dataclass, mo):
    ### CLASSES FOR THINGS
    @dataclass
    class Segment:
        time: float  # minutes
        conc: int  # millimolar
        flows: list  # pump_a, pump_b


    @dataclass
    class Syringe:
        name: str
        in_dia: float  # mm


    ### STATES FOR THINGS

    # Segment Builder States
    get_segs, set_segs = mo.state([])
    seg_added, set_seg_added = mo.state(False)

    # Pumps
    get_pumps, set_pumps = mo.state({})
    pump_confirmed, set_pump_confirmed = mo.state(False)
    pump_running, set_pump_running = mo.state(False)
    return (
        Segment,
        Syringe,
        get_pumps,
        get_segs,
        pump_confirmed,
        pump_running,
        seg_added,
        set_pump_confirmed,
        set_pump_running,
        set_pumps,
        set_seg_added,
        set_segs,
    )


@app.cell
def ui_elements(
    Syringe,
    add_seg,
    clear_segs,
    confirm_syringe_diam,
    mo,
    pumps,
    rm_last_seg,
):
    ### ADD NEW SYRINGES HERE IF NEEDED
    bd_20mL = Syringe(name="BD: 20 mL", in_dia=19.05)


    ### AND ADD THEM TO THIS LOOKUP
    def syringe_lookup(name):
        if name == bd_20mL.name:
            return bd_20mL


    #######################################################################
    ### DEFINE UI ELEMENTS
    #######################################################################
    select_pump_syringe = mo.ui.dropdown(
        options=[
            bd_20mL.name,
        ],
        value=bd_20mL.name,
    )

    select_port = mo.ui.dropdown(
        options=["/dev/cu.usbserial-2140"], value="/dev/cu.usbserial-2140"
    )

    select_flow_rate = mo.ui.number(0, 20, 0.1, value=10)

    select_pumpA_conc = mo.ui.number(0, 100, 5, value=0)

    select_pumpB_conc = mo.ui.number(0, 100, 5, value=100)

    confirm_parameters_button = mo.ui.button(
        label="CONFIRM AND SEND TO PUMP",
        on_change=lambda _: confirm_syringe_diam(
            pumps, syringe_lookup(select_pump_syringe.value).in_dia
        ),
    )

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
        add_seg_button,
        bd_20mL,
        clear_segs_button,
        confirm_parameters_button,
        rm_last_seg_button,
        select_flow_rate,
        select_port,
        select_pumpA_conc,
        select_pumpB_conc,
        select_pump_syringe,
        syringe_lookup,
    )


@app.cell
def functions(
    Segment,
    get_segs,
    seg_conc_box,
    seg_len_box,
    set_seg_added,
    set_segs,
):
    ##### FUNCTIONS
    def confirm_syringe_diam(pumps, diam):
        """
        Confirms pump settings and sends it to the pump. Right now the only setting
        is inner diameter of the syringe.
        """
        for pump in pumps:
            pump.syringe_diameter = diam


    def send_pump_flowrate(pumps, rates):
        for n, pump in enumerate(pumps):
            pump.pumping_rate = rates[n]


    def calculate_flowrates(conc_a, conc_b, conc_desired, total_flow):
        a_rate = (conc_desired - conc_b / conc_a) * total_flow
        b_rate = total_flow - a_rate
        return [a_rate, b_rate]


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


    def test(pump):
        print(pump.address)
    return (
        add_seg,
        calculate_flowrates,
        clear_segs,
        confirm_syringe_diam,
        rm_last_seg,
        send_pump_flowrate,
        test,
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
def pump_init(
    nesp_lib,
    select_port,
    select_pumpA_conc,
    select_pumpB_conc,
    set_pumps,
):
    ### NOTES AND SHIT
    #
    #   I EMPIRICALLY MEASURED THE FLOW RATE DUE TO GRAVITY IN MY SYSTEM
    #   Really just an approximate start point more than anything!
    #   Used 30 mL syringes, held at about 60-80 mm above the sample
    #   Tubing length used was 60.5 mm long, and the inner diameter is 0.51 mm
    #   Timing flow to end was about 8-8.25 seconds. So ~0.00745 m/s flow velocity
    #   Based on the diameter, this means a flow rate of about 0.15 ml/min
    #   Alternatively, 10.7 ml/hr, or 10700 uL/hr.

    # Initialize Pumps

    port = nesp_lib.Port(select_port.value, 19200)
    pump_a = nesp_lib.Pump(port, address=0)
    pump_b = nesp_lib.Pump(port, address=1)
    set_pumps({pump_a: select_pumpA_conc.value, pump_b: select_pumpB_conc.value})
    # set_pumps([])
    return port, pump_a, pump_b


@app.cell
def __(get_pumps):
    get_pumps()
    return


if __name__ == "__main__":
    app.run()
