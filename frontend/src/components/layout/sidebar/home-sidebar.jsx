import { ShopLinks } from '../shop-links';

export function HomeSidebar({ collections }) {
  return (
    <aside className='max-md:hidden col-span-4 h-screen sticky top-0 p-sides pt-top-spacing flex flex-col justify-between'>
      <div>
        <p className='italic tracking-tighter text-base'>Refined. Minimal. Never boring.</p>
        <div className='mt-5 text-base leading-tight'>
          <p>Furniture that speaks softly, but stands out loud.</p>
          <p>Clean lines, crafted with wit.</p>
          <p>Elegance with a wink — style first</p>
        </div>
      </div>
      <ShopLinks collections={collections} />
    </aside>
  );
}
