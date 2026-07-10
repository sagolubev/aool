export const scrollWorldConfig = {
  brand: { name: 'АУЛ', href: '#top' },
  hint: 'листайте — начнётся полёт',
  nav: true,
  crossfade: 0.12,
  connectors: [] as (string | null)[], // Architecture A — коннекторов нет
  sections: [
    {
      id: 'forest', label: 'Лес', still: '/scroll/forest.webp', clip: '/scroll/forest.mp4',
      accent: '#6a8a6b', eyebrow: '25 км от Уфы', title: 'Тишина начинается здесь.',
      body: 'Село Акбердино. Лес, воздух, покой — пространство с ощущением дома.',
      tags: ['Природа', 'Безопасность'],
    },
    {
      id: 'gate', label: 'Посёлок', still: '/scroll/gate.webp', clip: '/scroll/gate.mp4',
      accent: '#5a7a60', eyebrow: 'Родная земля', title: 'Пространство на традициях.',
      body: 'Единый архитектурный код, безбарьерная среда, высокий сервис.',
      tags: ['Родство'],
    },
    {
      id: 'alley', label: 'Аллея', still: '/scroll/alley.webp', clip: '/scroll/alley.mp4',
      accent: '#4a6a55', eyebrow: '25 гектаров', title: '103 дома, один ландшафт.',
      body: 'Центральная аллея, амфитеатр, пруд, беговые дорожки и сады.',
      tags: ['Среда', 'Развитие'],
    },
    {
      id: 'house', label: 'Дом', still: '/scroll/house.webp', clip: '/scroll/house.mp4',
      scroll: 2.0, linger: 0.45, accent: '#3a5a4a', eyebrow: 'Дом «Вода»',
      title: '362 м², два этажа.', body: 'Панорамное остекление, потолки до 4,7 м, террасы.',
      tags: ['Архитектура'],
    },
    {
      id: 'interior', label: 'Интерьер', still: '/scroll/interior.webp', clip: '/scroll/interior.mp4',
      scroll: 2.6, linger: 0.5, accent: '#2d4a3e', eyebrow: 'Внутри',
      title: 'Свет и простор.', body: 'Двусветная гостиная, камин, кухня-остров.',
      tags: ['Комфорт'],
    },
    {
      id: 'garden', label: 'Сад', still: '/scroll/garden.webp', clip: '/scroll/garden.mp4',
      scroll: 1.8, linger: 0.35, accent: '#2d4a3e', eyebrow: 'Приватность',
      title: 'Ваш собственный сад.', body: 'Терраса, BBQ-зона, фруктовые деревья, вид на воду.',
      tags: ['Отдых'],
      cta: {
        primary: { label: 'Выбрать дом', href: 'https://aool.space/doma/' },
        secondary: { label: 'О посёлке', href: '#manifesto' },
      },
    },
  ],
}
