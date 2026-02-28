import { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';
import { HEADERS } from '../../const.ts';
// import { data } from '../../mocks.ts';
import DownloadTable from '../download-table/DownloadTable.tsx';
import type { Data } from '../../types.ts';

function App() {
  const [data, setData] = useState([]);

  useEffect(() => {
    axios.get('/api') 
      .then(response => {
        setData(response.data);
      })
      .catch(error => {
        console.error('Ошибка при получении данных:', error);
      });
  }, []);

  return (
    <>
      <DownloadTable headers={HEADERS} data={data} />
      <table>
        <thead>
          <tr>
            {Object.values(HEADERS).map((header) => (<th>{header}</th>))}
          </tr>
        </thead>
        <tbody>
          {data.map((columnItem: Data) => (
            <tr>
              {((Object.keys(HEADERS)) as Array<keyof Data>).map((rowItem) => (<td>{columnItem[rowItem]}</td>))}
            </tr>
          ))}
        </tbody>
      </table>
    </>
  )
}

export default App;
