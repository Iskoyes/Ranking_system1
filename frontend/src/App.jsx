import { useState } from 'react';
import './App.css';

function App() {
  const [formData, setFormData] = useState({
    name: '',
    surname: '',
    year_of_birth: '',
    gender: '',
    event: '',
    result: '',
    date_of_competition: '',
    pool_length: '',
    fina_points: ''
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      [name]: value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch('http://localhost:5000/api/data', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
      });
      if (response.ok) {
        alert('Data submitted successfully!');
      } else {
        const errorData = await response.json();
        alert(`Failed to submit data: ${errorData.message}`);
      }
    } catch (error) {
      console.error('Error:', error);
      alert('An error occurred');
    }
  };

  return (
    <div className="App">
      <h1>Data Entry Form</h1>
      <form onSubmit={handleSubmit}>
        <div>
          <label>Date of Competition: </label>
          <input type="text" name="date_of_competition" value={formData.date_of_competition} onChange={handleChange} tabindex="1"/>
        </div>
        <div>
          <label>Pool Length: </label>
          <select name="pool_length" value={formData.pool_length} onChange={(e) => handleChange({ target: { name: 'pool_length', value: parseInt(e.target.value) } })} tabindex="2">
            <option value="25">25</option>
            <option value="50" selected="selected">50</option>
          </select>
        </div><br></br>
        <div>
          <label>Event: </label>
          <input type="text" name="event" value={formData.event} onChange={handleChange} tabindex="3" />
        </div>
        <div>
          <label>Full Name: </label>
          <input type="text" name="full_name" value={formData.full_name} onChange={handleChange} tabindex="4" />
        </div>
        <div>
          <label>Year of Birth: </label>
          <input type="number" name="year_of_birth" value={formData.year_of_birth} onChange={handleChange} tabindex="5" />
        </div>
        <div>
          <label>Gender: </label>
          <select name="gender" value={formData.gender} onChange={handleChange} tabindex="6">
            <option value="M">M</option>
            <option selected value="F">F</option>
          </select>
        </div>
        <div>
          <label>Result: </label>
          <input type="text" name="result" value={formData.result} onChange={handleChange} tabindex="7" />
        </div><br></br>
        <button type="submit" tabindex="8">Submit</button>
      </form>
    </div>
  );
}

export default App;