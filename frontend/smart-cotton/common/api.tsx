import axios, { AxiosResponse } from "axios";

const axiosApi = axios.create({
    timeout: 300000,
    withCredentials: false,
    baseURL: process.env.REACT_APP_BACKEND_URL,
});

export const api = {

};