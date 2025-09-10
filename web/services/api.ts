import axios from 'axios';
import { BusinessPlan } from '../types/business_plan';

const API_BASE_URL = 'http://192.168.1.106:8000';

export const getRandomPlan = async (): Promise<BusinessPlan | null> => {
  try {
    const response = await axios.get(`${API_BASE_URL}/random_plan`);
    return response.data || null;
  } catch (error) {
    console.error('Error fetching random plan:', error);
    throw error;
  }
};
