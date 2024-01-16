import marimo

__generated_with = "0.1.76"
app = marimo.App()


@app.cell
def __(mo):
    mo.md(
        f"""

        ## Pump Program Builder
        Use this to design a series of concentrations while imaging. 

        """
         )
    return


@app.cell
def __(dataclass, mo):
    @dataclass
    class Segment:
        time: float      # minutes
        conc: int        # millimolar

    get_segs, set_segs = mo.state([])
    seg_added, set_seg_added = mo.state(False)
    return Segment, get_segs, seg_added, set_seg_added, set_segs


@app.cell
def __(mo, seg_added):
    # Refresh the entry form whenever a task is added
    seg_added

    seg_len_box = mo.ui.number(0, 10, step=0.25, value=0)
    seg_conc_box = mo.ui.number(0,100,step=5, value=0)
    return seg_conc_box, seg_len_box


@app.cell
def __(add_seg_button, clear_segs_button, mo, seg_conc_box, seg_len_box):
    mo.vstack([
        mo.hstack(
            [mo.md("Segment length: "), seg_len_box, mo.md(" (min)")], 
            justify="start"
        ),
        mo.hstack(
            [mo.md("Concentration: "), seg_conc_box, mo.md(" (mM)")],
            justify="start"
        ),
        mo.hstack(
            [add_seg_button, clear_segs_button], justify="start"
        )
        
    ])
    return


@app.cell
def __(Segment, mo, seg_conc_box, seg_len_box, set_seg_added, set_segs):
    def add_seg():
        if seg_len_box.value > 0 and seg_conc_box.value > 0:
            
            set_segs(lambda v: v + [Segment(seg_len_box.value, seg_conc_box.value)])
            set_seg_added(True)

    def clear_segs():
        set_segs([])

    add_seg_button = mo.ui.button(
        label="add segment",
        on_change=lambda _: add_seg(),
    )

    clear_segs_button = mo.ui.button(
        label="clear all segments",
        on_change=lambda _: clear_segs()
    )
    return add_seg, add_seg_button, clear_segs, clear_segs_button


@app.cell
def __(get_segs):
    get_segs()
    return


@app.cell
def __():
    import marimo as mo
    import numpy as np
    import serial
    from dataclasses import dataclass
    return dataclass, mo, np, serial


@app.cell
def __():
    # Configuration
    #mo.vstack([
    #    mo.hstack(
    #        [mo.md("Segment length: "), seg_len_box, mo.md(" (min)")], 
    #        justify="start"
    #    ),
    #    mo.hstack(
    #        [mo.md("Concentration: "), seg_conc_box, mo.md(" (mM)")],
    #        justify="start"
    #    )
    #    
    #])

    #pump_a = mo.ui.text(value="0")
    #mo.md(f"Concentration of Pump 1: {pump_a} mM")
    #pump_b
    # flow_rate
    # desired_conc.value = pump_a.value*x + pump_b.value*(1-x)
    # dc_.value = pb.value + (pa.value-pb.value)*x
    #a_rate = float((int(desired_conc.value) - int(pump_b.value))/(int(pump_a.value) - #int(pump_b.value)))
    #mo.md(f"{a_rate}")
    return


if __name__ == "__main__":
    app.run()
