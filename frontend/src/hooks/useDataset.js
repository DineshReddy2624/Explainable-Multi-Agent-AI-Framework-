import { useContext } from 'react';
import { DatasetContext } from '../context/DatasetContext';

export const useDataset = () => {
  return useContext(DatasetContext);
};
