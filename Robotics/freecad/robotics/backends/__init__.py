from importlib import import_module

BACKENDS = {
    "pinocchio": ("freecad.robotics.backends.pinocchio",
                  "PinocchioBackend"),
    "tesseract": ("freecad.robotics.backends.tesseract",
                  "TesseractBackend"),
    "ikpy":      ("freecad.robotics.backends.ikpy",
                  "IkpyBackend"),
    "numpy_dls": ("freecad.robotics.backends.numpy_dls",
                  "NumpyDLSBackend"),
}

KIN_LIB_NAMES = list(BACKENDS)


def load_kinematics_lib(name):
    if name not in BACKENDS:
        raise ValueError(f"unknown kinematics lib: {name}")
    mod, cls = BACKENDS[name]
    return getattr(import_module(mod), cls)
