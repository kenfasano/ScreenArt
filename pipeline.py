import random
from . import log
from typing import Callable, Dict, List

DEFAULT_TRANSFORMER_COUNT: int = 3

def get_all_transformers_dict() -> Dict[str, Callable]:
    """
    Lazily imports transformers and returns a dictionary mapping
    lowercase class names to the class objects.
    
    CRITICAL: This function isolates the imports. Do not move these imports
    to the top of the file, or the circular dependency error will return.
    """
    from Transformers.RasterTransformers import (
        AnamorphicTransformer,
        ColormapTransformer,
        DataMoshTransformer,
        DuotoneTransformer,
        FisheyeTransformer,
        FluidWarpTransformer,
        FractalWarpTransformer,
        GlitchWarpTransformer,
        HalftoneTransformer,
        # InvertRGBTransformer, # Removed: Causing errors
        MeltMorphTransformer,
        NullTransformer,
        PosterizationTransformer,
        RadialWarpTransformer,
        SwirlWarpTransformer,
        ThreeDExtrusionTransformer,
        ThermalImagingTransformer,
        TritoneTransformer,
        WatercolorTransformer,
        XrayTransformer,
    )

    all_transformers: List[Callable] = [
        AnamorphicTransformer,
        ColormapTransformer,
        DataMoshTransformer,
        DuotoneTransformer,
        FisheyeTransformer,
        FluidWarpTransformer,
        FractalWarpTransformer,
        GlitchWarpTransformer,
        HalftoneTransformer,
        # InvertRGBTransformer,
        MeltMorphTransformer,
        NullTransformer,
        PosterizationTransformer,
        RadialWarpTransformer,
        SwirlWarpTransformer,
        ThermalImagingTransformer,
        ThreeDExtrusionTransformer,
        TritoneTransformer,
        WatercolorTransformer,
        XrayTransformer,
    ]

    return {
        str(transformer.__name__).lower(): transformer
        for transformer in all_transformers
    }


class Pipeline:
    def __init__(self, config: dict | None):
        self.config = config if config is not None else {}
        
        # 1. Fetch the dictionary using the function (Lazy Load)
        all_transformers_dict = get_all_transformers_dict()
        current_transformers_dict = all_transformers_dict.copy()

        # 2. Check for an 'include' list and filter if present
        include_list = self.config.get("include")
        if include_list:
            include_list_lower = [str(x).lower() for x in include_list]
            current_transformers_dict = {
                name: cls for name, cls in current_transformers_dict.items()
                if name in include_list_lower
            }

        # 3. Check for an 'exclude' list and filter if present
        exclude_list = self.config.get("exclude")
        if exclude_list:
            exclude_list_lower = [str(x).lower() for x in exclude_list]
            current_transformers_dict = {
                name: cls for name, cls in current_transformers_dict.items()
                if name not in exclude_list_lower
            }

        # 4. Filter item out 'NullTransformer' if there is more than one item remaining.
        if (len(current_transformers_dict) > 1 and 
        "nulltransformer" in current_transformers_dict):
            del current_transformers_dict["nulltransformer"]

        # 5. Use the filtered dictionary for selection
        transformers = list(current_transformers_dict.items())
        
        # Handle the case where the dictionary might be empty after filtering
        if not transformers:
            self.functions = []
            log.warning("No transformers available after applying include/exclude filters.")
            return

        self.transformer_count = self.config.get("transformer_count",  DEFAULT_TRANSFORMER_COUNT)
        log.info(f"{self.transformer_count=}")

        # Get the available transformer names
        transformer_population = [name for name, _ in transformers]
        population_size = len(transformer_population)

        if not isinstance(self.transformer_count, int) or self.transformer_count < 0:
            log.warning(f"Invalid transformer_count '{self.transformer_count}', using default {DEFAULT_TRANSFORMER_COUNT}")
            self.transformer_count = DEFAULT_TRANSFORMER_COUNT

        num_to_sample = min(self.transformer_count, population_size)
        
        if population_size > 0:
            chosen_names = random.sample(transformer_population, k=num_to_sample)
        else:
            chosen_names = []
            log.warning("No transformers available after applying include/exclude filters.")
            return

        self.functions: list[Callable] = [
            all_transformers_dict[name]() for name in chosen_names
        ]

    def get_transformers(self):
        return self.functions
