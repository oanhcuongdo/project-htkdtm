export function mapLinks(latitude: number, longitude: number) {
  if (
    !Number.isFinite(latitude) ||
    !Number.isFinite(longitude) ||
    Math.abs(latitude) > 90 ||
    Math.abs(longitude) > 180
  )
    return null;
  const point = `${latitude},${longitude}`;
  const bbox = [
    Math.max(-180, longitude - 0.01),
    Math.max(-90, latitude - 0.01),
    Math.min(180, longitude + 0.01),
    Math.min(90, latitude + 0.01),
  ].join(",");
  return {
    embed: `https://www.openstreetmap.org/export/embed.html?${new URLSearchParams({ bbox, layer: "mapnik", marker: point })}`,
    map: `https://www.openstreetmap.org/?${new URLSearchParams({ mlat: String(latitude), mlon: String(longitude) })}#map=16/${latitude}/${longitude}`,
    directions: `https://www.google.com/maps/dir/?${new URLSearchParams({ api: "1", destination: point })}`,
  };
}
