import { SERVICE_CAPABILITIES } from "@/lib/services";

function groupByCategory() {
  const groups: { category: string; items: typeof SERVICE_CAPABILITIES }[] = [];
  for (const service of SERVICE_CAPABILITIES) {
    let group = groups.find((g) => g.category === service.category);
    if (!group) {
      group = { category: service.category, items: [] };
      groups.push(group);
    }
    group.items.push(service);
  }
  return groups;
}

export default function ServicesGrid() {
  const groups = groupByCategory();
  return (
    <div className="services-grouped">
      {groups.map((group) => (
        <div className="services-group" key={group.category}>
          <h3 className="services-group-label">{group.category}</h3>
          <div className="grid grid-3" style={{ gap: "1.5rem" }}>
            {group.items.map((service) => (
              <div className="card" key={service.slug} id={service.slug}>
                <h4>{service.name}</h4>
                <p>{service.blurb}</p>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
