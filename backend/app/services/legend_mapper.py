from typing import Dict, Any, Tuple
from ..utils.logger import logger

class LegendMapper:
    """
    Standard ISA-5.1 P&ID legend dictionary and mapping engine.
    Maps prefix and detected symbol to standardized Component Name and Category.
    """

    DEFAULT_LEGEND = {
        # Instruments - Pressure
        "PT": {"name": "Pressure Transmitter", "type": "Instrument", "symbol_class": "PT"},
        "PI": {"name": "Pressure Indicator", "type": "Instrument", "symbol_class": "PI"},
        "PIC": {"name": "Pressure Indicating Controller", "type": "Instrument", "symbol_class": "PIC"},
        "PIT": {"name": "Pressure Indicating Transmitter", "type": "Instrument", "symbol_class": "PIT"},
        "PDT": {"name": "Pressure Differential Transmitter", "type": "Instrument", "symbol_class": "PDT"},
        "PSV": {"name": "Pressure Safety Valve", "type": "Valve", "symbol_class": "PSV"},
        "PRV": {"name": "Pressure Relief Valve", "type": "Valve", "symbol_class": "PRV"},
        "PCV": {"name": "Pressure Control Valve", "type": "Valve", "symbol_class": "PCV"},

        # Instruments - Temperature
        "TT": {"name": "Temperature Transmitter", "type": "Instrument", "symbol_class": "TT"},
        "TI": {"name": "Temperature Indicator", "type": "Instrument", "symbol_class": "TI"},
        "TIC": {"name": "Temperature Indicating Controller", "type": "Instrument", "symbol_class": "TIC"},
        "TE": {"name": "Temperature Element / Thermocouple", "type": "Instrument", "symbol_class": "TE"},
        "TCV": {"name": "Temperature Control Valve", "type": "Valve", "symbol_class": "TCV"},

        # Instruments - Flow
        "FT": {"name": "Flow Transmitter", "type": "Instrument", "symbol_class": "FT"},
        "FI": {"name": "Flow Indicator", "type": "Instrument", "symbol_class": "FI"},
        "FIC": {"name": "Flow Indicating Controller", "type": "Instrument", "symbol_class": "FIC"},
        "FE": {"name": "Flow Element / Orifice", "type": "Instrument", "symbol_class": "FE"},
        "FCV": {"name": "Flow Control Valve", "type": "Valve", "symbol_class": "FCV"},

        # Instruments - Level
        "LT": {"name": "Level Transmitter", "type": "Instrument", "symbol_class": "LT"},
        "LI": {"name": "Level Indicator", "type": "Instrument", "symbol_class": "LI"},
        "LIC": {"name": "Level Indicating Controller", "type": "Instrument", "symbol_class": "LIC"},
        "LV": {"name": "Level Valve", "type": "Valve", "symbol_class": "LV"},
        "LCV": {"name": "Level Control Valve", "type": "Valve", "symbol_class": "LCV"},
        "LG": {"name": "Level Gauge", "type": "Instrument", "symbol_class": "LG"},

        # Automated & Manual Valves
        "XV": {"name": "Emergency Shutdown Valve", "type": "Valve", "symbol_class": "XV"},
        "HV": {"name": "Manual Hand Valve", "type": "Valve", "symbol_class": "HV"},
        "MOV": {"name": "Motor Operated Valve", "type": "Valve", "symbol_class": "MOV"},
        "SOV": {"name": "Solenoid Operated Valve", "type": "Valve", "symbol_class": "SOV"},
        "BDV": {"name": "Blowdown Valve", "type": "Valve", "symbol_class": "BDV"},
        "V": {"name": "Vessel / General Valve", "type": "Equipment", "symbol_class": "Vessel"},

        # Major Equipment
        "P": {"name": "Centrifugal Pump", "type": "Equipment", "symbol_class": "Pump"},
        "PU": {"name": "Pump", "type": "Equipment", "symbol_class": "Pump"},
        "PUMP": {"name": "Pump", "type": "Equipment", "symbol_class": "Pump"},
        "TK": {"name": "Storage Tank", "type": "Equipment", "symbol_class": "Tank"},
        "T": {"name": "Tower / Tank", "type": "Equipment", "symbol_class": "Tank"},
        "E": {"name": "Heat Exchanger", "type": "Equipment", "symbol_class": "Exchanger"},
        "C": {"name": "Compressor", "type": "Equipment", "symbol_class": "Compressor"},
        "CMP": {"name": "Compressor", "type": "Equipment", "symbol_class": "Compressor"},
        "M": {"name": "Electric Motor", "type": "Equipment", "symbol_class": "Motor"},
        "K": {"name": "Compressor", "type": "Equipment", "symbol_class": "Compressor"},
        "D": {"name": "Drum / Vessel", "type": "Equipment", "symbol_class": "Vessel"},
        "F": {"name": "Filter / Strainer", "type": "Equipment", "symbol_class": "Filter"},

        # Connectors
        "CONN": {"name": "Off-Page Connector", "type": "Connector", "symbol_class": "Connector"},
        "OPC": {"name": "Off-Page Connector", "type": "Connector", "symbol_class": "Connector"},
    }

    def __init__(self, custom_legend: Dict[str, Dict[str, str]] = None):
        self.legend = dict(self.DEFAULT_LEGEND)
        if custom_legend:
            self.legend.update(custom_legend)

    def identify_component(
        self,
        prefix: str,
        symbol_class: str = "",
        symbol_category: str = ""
    ) -> Dict[str, str]:
        """
        Combines parsed prefix, detected symbol class, and legend to produce:
        - component_name (e.g., 'Pressure Transmitter')
        - component_type (e.g., 'Instrument')
        - resolved_class (e.g., 'PT')
        """
        cleaned_prefix = prefix.upper().strip()
        
        if cleaned_prefix in self.legend:
            entry = self.legend[cleaned_prefix]
            return {
                "component_name": entry["name"],
                "component_type": entry["type"],
                "resolved_class": entry["symbol_class"]
            }

        # Fallback based on detected symbol if available
        if symbol_class in ["Valve", "FCV", "PSV", "LV", "XV"]:
            return {
                "component_name": f"{cleaned_prefix} Valve" if cleaned_prefix else "Pipeline Valve",
                "component_type": "Valve",
                "resolved_class": symbol_class
            }
        elif symbol_class in ["Pump", "Equipment"]:
            return {
                "component_name": f"{cleaned_prefix} Equipment" if cleaned_prefix else "Process Equipment",
                "component_type": "Equipment",
                "resolved_class": symbol_class
            }
        elif symbol_class in ["Instrument"]:
            return {
                "component_name": f"{cleaned_prefix} Instrument" if cleaned_prefix else "Process Instrument",
                "component_type": "Instrument",
                "resolved_class": symbol_class
            }

        # General category fallback
        return {
            "component_name": f"P&ID Component ({cleaned_prefix})" if cleaned_prefix else "P&ID Component",
            "component_type": symbol_category or "Instrument",
            "resolved_class": symbol_class or "generic"
        }
