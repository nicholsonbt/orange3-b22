from datetime import datetime




class MetaKeyException(Exception):
    pass


class MetaFormatter:
    class FileFormat:
        NEA_TXT = 0
        NEA = 1


    class Default:
        @staticmethod
        def ERROR(*values):
            # Raise the last caught exception.
            raise

        @staticmethod
        def NONE(*values):
            return None, None
        
        @staticmethod
        def BASIC(*values):
            return None, " ".join(values)
        

    FUNCS = {
        "Scan" : lambda *values: (None, " ".join(values)),

        "Project" : lambda *values: (None, " ".join(values)),

        "Description" : lambda *values: (None, " ".join(values)),

        "Date" : lambda date, time: (None, datetime.strptime(date + " " + time, '%d/%m/%Y %H:%M:%S')),

        "Reference" : lambda *values: (None, " ".join(values)),

        "Scanner Center Position (X, Y)" : lambda units, x, y: ("Real Center", {
                "Units" : units[1:-1],
                "X" : float(x),
                "Y" : float(y),
            }),

        "Rotation" : lambda units, theta: ("Angle", {
                "Units" : units[1:-1],
                "Theta" : float(theta),
            }),

        "Scan Area (X, Y, Z)" : lambda units, x, y, z: ("Real Area", {
                "Units" : units[1:-1],
                "X" : float(x),
                "Y" : float(y),
                "Z" : float(z),
            }),

        "Pixel Area (X, Y, Z)" : lambda units, x, y, z: ("Pixel Area", {
                "Units" : units[1:-1],
                "X" : float(x),
                "Y" : float(y),
                "Z" : float(z),
            }),

        "Interferometer Center/Distance" : lambda units, center, distance: (None, {
                "Units" : units[1:-1],
                "Center" : float(center),
                "Distance" : float(distance),
            }),

        "Averaging" : lambda *values: (None, " ".join(values)),

        "Integration time" : lambda units, value: (None, {
                "Units" : units[1:-1],
                "Value" : float(value),
            }),

        "Wavenumber Scaling" : lambda *values: (None, " ".join(values)),

        "Laser Source" : lambda *values: (None, " ".join(values)),

        "Detector" : lambda *values: (None, " ".join(values)),

        "Target Wavelength" : lambda units: (None, units[1:-1]),

        "Demodulation Mode" : lambda *values: (None, " ".join(values)),

        "Tip Frequency" : lambda units, frequency: (None, {
                "Units" : units[1:-1],
                "Frequency" : float(frequency.replace(",", "")),
            }),

        "Tip Amplitude" : lambda units, amplitude: (None, {
                "Units" : units[1:-1],
                "Amplitude" : float(amplitude),
            }),

        "Tapping Amplitude" : lambda units, amplitude: (None, {
                "Units" : units[1:-1],
                "Amplitude" : float(amplitude),
            }),

        "Modulation Frequency" : lambda units, frequency: (None, {
                "Units" : units[1:-1],
                "Frequency" : float(frequency),
            }),

        "Modulation Amplitude" : lambda units, amplitude: (None, {
                "Units" : units[1:-1],
                "Amplitude" : float(amplitude),
            }),

        "Modulation Offset" : lambda units, offset: (None, {
                "Units" : units[1:-1],
                "Offset" : float(offset),
            }),

        "Setpoint" : lambda units, setpoint: (None, {
                "Units" : units[1:-1],
                "Setpoint" : float(setpoint),
            }),

        "Regulator (P, I, D)": lambda p, i, d: (None, {
                "P" : float(p),
                "I" : float(i),
                "D" : float(d),
            }),

        "Tip Potential" : lambda units, potential: (None, {
                "Units" : units[1:-1],
                "Potential" : float(potential),
            }),

        "M1A Scaling" : lambda units, scaling: (None, {
                "Units" : units[1:-1],
                "Scaling" : float(scaling),
            }),

        "M1A Cantilever Factor" : lambda *values: (None, " ".join(values)),

        "Version" : lambda *values: (None, " ".join(values)),
    }
    

    @staticmethod
    def format(key, values, file_format, default_func=Default.ERROR):
        try:
            return MetaFormatter._format(key, values, file_format)
        except MetaKeyException as e:
            return default_func(*values)

    
    @staticmethod
    def _format(key, values, file_format):
        try:
            func = MetaFormatter.FUNCS[key]
        except KeyError:
            raise MetaKeyException(f"MetaFormatter has no method to convert '{key}'")

        if isinstance(func, dict):
            try:
                func = func[file_format]
            except KeyError:
                raise MetaKeyException(f"MetaFormatter has no method to convert '{key}'")

        if callable(func):
            return func(*values)
        
        raise MetaKeyException(f"MetaFormatter has no method to convert '{key}'")
