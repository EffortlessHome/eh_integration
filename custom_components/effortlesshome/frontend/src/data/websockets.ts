import {
  effortlesshomeConfig,
  effortlesshomeModeConfig,
  effortlesshomeSensor,
  Dictionary,
  effortlesshomeUser,
  EArmModes,
  effortlesshomeAutomation,
  effortlesshomeArea,
  SensorGroup,
  HomeAssistant,
} from '../types';

export const fetchConfig = (hass: HomeAssistant): Promise<effortlesshomeConfig> =>
  hass.callWS({
    type: 'effortlesshome/config',
  });

export const fetchSensors = (hass: HomeAssistant): Promise<Dictionary<effortlesshomeSensor>> =>
  hass.callWS({
    type: 'effortlesshome/sensors',
  });

export const fetchUsers = (hass: HomeAssistant): Promise<Dictionary<effortlesshomeUser>> =>
  hass.callWS({
    type: 'effortlesshome/users',
  });

export const fetchAutomations = (hass: HomeAssistant): Promise<Dictionary<effortlesshomeAutomation>> =>
  hass.callWS({
    type: 'effortlesshome/automations',
  });

export const fetchSensorGroups = (hass: HomeAssistant): Promise<Dictionary<SensorGroup>> =>
  hass.callWS({
    type: 'effortlesshome/sensor_groups',
  });

export const saveConfig = (hass: HomeAssistant, config: Partial<effortlesshomeConfig>): Promise<boolean> => {
  return hass.callApi('POST', 'effortlesshome/config', config);
};

export const saveModeConfig = (
  hass: HomeAssistant,
  config: Partial<effortlesshomeModeConfig> & { mode: EArmModes }
): Promise<boolean> => {
  return hass.callApi('POST', 'effortlesshome/mode', config);
};

export const saveSensor = (
  hass: HomeAssistant,
  config: Partial<effortlesshomeSensor> & { entity_id: string }
): Promise<boolean> => {
  return hass.callApi('POST', 'effortlesshome/sensors', config);
};

export const deleteSensor = (hass: HomeAssistant, entity_id: string): Promise<boolean> => {
  return hass.callApi('POST', 'effortlesshome/sensors', {
    entity_id: entity_id,
    remove: true,
  });
};

export const saveUser = (hass: HomeAssistant, config: Partial<effortlesshomeUser>): Promise<boolean> => {
  return hass.callApi('POST', 'effortlesshome/users', config);
};

export const deleteUser = (hass: HomeAssistant, user_id: string): Promise<boolean> => {
  return hass.callApi('POST', 'effortlesshome/users', {
    user_id: user_id,
    remove: true,
  });
};

export const saveAutomation = (hass: HomeAssistant, config: Partial<effortlesshomeAutomation>): Promise<boolean> => {
  return hass.callApi('POST', 'effortlesshome/automations', config);
};

export const deleteAutomation = (hass: HomeAssistant, automation_id: string): Promise<boolean> => {
  return hass.callApi('POST', 'effortlesshome/automations', {
    automation_id: automation_id,
    remove: true,
  });
};

export const fetchAreas = (hass: HomeAssistant): Promise<Dictionary<effortlesshomeArea>> =>
  hass.callWS({
    type: 'effortlesshome/areas',
  });

export const saveArea = (hass: HomeAssistant, config: Partial<effortlesshomeArea>): Promise<boolean> => {
  return hass.callApi('POST', 'effortlesshome/area', config);
};

export const deleteArea = (hass: HomeAssistant, area_id: string): Promise<boolean> => {
  return hass.callApi('POST', 'effortlesshome/area', {
    area_id: area_id,
    remove: true,
  });
};

export const saveSensorGroup = (hass: HomeAssistant, config: Partial<SensorGroup>): Promise<boolean> => {
  return hass.callApi('POST', 'effortlesshome/sensor_groups', config);
};

export const deleteSensorGroup = (hass: HomeAssistant, group_id: string): Promise<boolean> => {
  return hass.callApi('POST', 'effortlesshome/sensor_groups', {
    group_id: group_id,
    remove: true,
  });
};
