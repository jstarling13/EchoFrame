import { SERVICE_CAPABILITIES } from "@/lib/services";

export default function ServicesGrid() {
  return (
    <div className="grid grid-3" style={{ gap: "1.5rem" }}>
      {SERVICE_CAPABILITIES.map((service) => (
        <div className="card" key={service.slug} id={service.slug}>
          <p className="eyebrow">{service.category}</p>
          <h3>{service.name}</h3>
          <p>{service.blurb}</p>
        </div>
      ))}
    </div>
  );
}
