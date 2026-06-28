from dataclasses import dataclass

from ..scenario_generation.risk_factor_evolution import RiskFactorEvolution
from ..scenario_generation.brownian_motion import BrownianMotion
from ..scenario_generation.geometric_brownian_motion import GeometricBrownianMotion
from ..scenario_generation.hw1f import HW1F


@dataclass
class RiskFactor:
    name: str
    asset_class: str
    asset_type: str
    currency: str
    simulated: bool
    model: RiskFactorEvolution
    model_name: str
    reference: str

    def __init__(self, name, asset_class, asset_type, currency, simulated, model_name, **kwargs):
        self.name = name
        self.asset_class = asset_class
        self.asset_type = asset_type
        self.currency = currency
        self.simulated = simulated
        self.model_name = model_name
        self.model = None
        self.reference = None

        if simulated:
            if model_name == 'BM':
                self.model = BrownianMotion(name)
            elif model_name == 'GBM':
                self.model = GeometricBrownianMotion(name)
            elif model_name == 'HW1F':
                self.model = HW1F(name)
            elif model_name == 'NOT_AVAILABLE':
                self.model = None
            else:
                raise ValueError(
                    f'Model {model_name} for risk factor {name} is not implemented.')

        if asset_type[:6] == 'SPREAD':
            self.reference = kwargs.get('reference')
