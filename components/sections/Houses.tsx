const houses = [
  { name: 'Земля', area: 226, floors: 1 },
  { name: 'Огонь', area: 321, floors: 2 },
  { name: 'Воздух', area: 428, floors: 1 },
  { name: 'Вода', area: 362, floors: 2 },
]

export function Houses() {
  return (
    <section id="houses" className="sec">
      <h2>Дома</h2>
      <p className="lead">Стоимость от 38 млн ₽. Четыре типа в едином архитектурном стиле.</p>
      <ul className="grid">
        {houses.map((h) => (
          <li key={h.name} className="card">
            <h3>Дом «{h.name}»</h3>
            <p>{h.area} м² · {h.floors} эт.</p>
          </li>
        ))}
      </ul>
    </section>
  )
}
