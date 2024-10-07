import logging
from homeassistant.core import HomeAssistant
from homeassistant.components.recorder.models import state
from homeassistant.util import dt as dt_util
from datetime import timedelta
import numpy as np
from sklearn.cluster import KMeans
from homeassistant.components.recorder.models import state
from homeassistant.util import dt as dt_util
from datetime import timedelta
from homeassistant.core import HomeAssistant, ServiceCall, callback

_LOGGER = logging.getLogger(__name__)


class HASSComponent:
    # Class-level property to hold the hass instance
    hass_instance = None

    @classmethod
    def set_hass(cls, hass: HomeAssistant):
        cls.hass_instance = hass

    @classmethod
    def get_hass(cls):
        return cls.hass_instance


async def async_setup(hass: HomeAssistant, config):
    """Set up the AI Optimizer component."""

    HASSComponent.set_hass(hass)

    # Register a service that can be called from the frontend

    @callback
    async def createoptimizehomeservice(call: ServiceCall):
        await optimize_home(call)

    hass.services.async_register(
        "ai_optimizer", "createoptimizehomeservice", optimize_home
    )
    return True


async def optimize_home(call):
    """Handler for the optimization service."""
    entity_id = call.data.get("entity_id")

    _LOGGER.debug("In optimize_home. EntityID:" + entity_id)

    hass = HASSComponent.get_hass()

    history_data = await fetch_history_data(hass, entity_id, 30)
    if not history_data:
        _LOGGER.warning("No history data found for %s", entity_id)
        return

    # Analyze the data
    labels = analyze_data(history_data)

    # Generate recommendations
    recommendations = generate_recommendations(labels, entity_id)

    # Log or notify the recommendations
    for recommendation in recommendations:
        _LOGGER.info("Recommended automation: %s", recommendation)


def fetch_history_data(hass, entity_id, days=30):
    """Fetch historical data for an entity."""
    _LOGGER.debug("In fetch history data")
    start_time = dt_util.utcnow() - timedelta(days=days)
    history_data = hass.states.async_all(entity_id=entity_id, start_time=start_time)
    return history_data


def analyze_data(history_data):
    """Analyze the history data using KMeans clustering to detect patterns."""

    _LOGGER.debug("In analyze data")

    timestamps = [state.last_updated for state in history_data]
    values = [state.state for state in history_data]

    # Convert timestamps and values to numpy arrays
    X = np.array(list(zip(timestamps, values)))

    # Apply KMeans clustering
    kmeans = KMeans(n_clusters=3)
    kmeans.fit(X)

    # Return the clustering labels
    return kmeans.labels_


def generate_recommendations(cluster_labels, entity_id):
    """Generate automation recommendations based on detected patterns."""
    recommendations = []

    _LOGGER.debug("In generate recommendations")

    for label in set(cluster_labels):
        if label == 0:  # Example: On/Off pattern detected
            recommendations.append(
                {
                    "automation": f"Turn {entity_id} on at specific times",
                    "trigger": "time",
                    "action": f"turn on {entity_id}",
                }
            )
    return recommendations
