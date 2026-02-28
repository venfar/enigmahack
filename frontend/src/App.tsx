import { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';
// import {data} from './mocks.ts';

function App() {
  const [data, setData] = useState([]);

  useEffect(() => {
    axios.get('https://jsonplaceholder.typicode.com/posts') 
      .then(response => {
        setData(response.data);
      })
      .catch(error => {
        console.error('Ошибка при получении данных:', error);
      });
  }, []);

  return (
    <table>
      <thead>
        <tr>
          <th>Дата</th>
          <th>ФИО</th>
          <th>Объект</th>
          <th>Телефон</th>
          <th>Email</th>
          <th>Заводские номера</th>
          <th>Тип приборов</th>
          <th>Эмоциональный окрас</th>
          <th>Суть вопроса</th>
        </tr>
      </thead>
      <tbody>
        {data.map((columnItem: object) => (
          <tr>
            {Object.values(columnItem).map((rowItem) => (<td>{rowItem}</td>))}
          </tr>
        ))}
      </tbody>
    </table>
  )
}

export default App;
