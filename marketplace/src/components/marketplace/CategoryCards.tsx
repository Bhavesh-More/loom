import { categories } from '../../data/marketplace'
import Icon from '../Icon'

function CategoryCards() {
  return (
    <section className="category-section">
      <div className="category-grid">
        {categories.map((category) => (
          <article className={category.className} key={category.title}>
            <h3>{category.title}</h3>
            <div className="category-icons">
              {category.icons.map((item) => (
                <span className="category-icon" key={`${category.title}-${item.icon}`}>
                  <Icon icon={item.icon} className={item.className} />
                </span>
              ))}
            </div>
            <p>{category.description}</p>
          </article>
        ))}
      </div>
    </section>
  )
}

export default CategoryCards
