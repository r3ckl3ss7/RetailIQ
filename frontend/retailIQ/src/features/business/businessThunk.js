import api from "../../services/api";
import {
  fetchStart,
  fetchFailure,
  fetchSuccess,
  createFailure,
  createStart,
  createSuccess,
  fetchBusinessesSuccess,
  updateFailure,
  updateStart,
  updateSuccess,
  deleteSuccess,
  deleteStart,
  deleteFailure,
} from "./businessSlice";
export const create_business = (data) => async (dispatch) => {
  dispatch(createStart());
  try {
    const response = await api.post("/user/business", data);
    const new_business = response.data;
    dispatch(createSuccess(new_business));
  } catch (err) {
    dispatch(createFailure(err.response?.data || { error: err.message }));
  }
};
export const fetch_user_businesses = (userId) => async (dispatch) => {
  dispatch(fetchStart());
  try {
    const response = await api.get(`/user/${userId}`);
    dispatch(fetchBusinessesSuccess(response.data.businesses));
  } catch (err) {
    dispatch(fetchFailure(err.response?.data || { error: err.message }));
  }
};
export const fetch_business = (userId, businessId) => async (dispatch) => {
  dispatch(fetchStart());
  try {
    const response = await api.get(`/user/${userId}/${businessId}`);
    dispatch(fetchSuccess(response.data));
  } catch (err) {
    dispatch(fetchFailure(err.response?.data || { error: err.message }));
  }
};
export const update_business = (data, businessId) => async (dispatch) => {
  dispatch(updateStart());
  try {
    const response = await api.patch(`/user/business/${businessId}`, data);
    dispatch(updateSuccess(response.data));
  } catch (err) {
    dispatch(updateFailure(err.response?.data || { error: err.message }));
  }
};
export const delete_business = (businessId) => async (dispatch) => {
  dispatch(deleteStart());
  try {
    await api.delete(`/user/business/${businessId}`);
    dispatch(deleteSuccess(businessId));
  } catch (err) {
    dispatch(deleteFailure(err.message));
  }
};
