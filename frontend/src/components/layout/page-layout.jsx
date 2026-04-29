export const PageLayout = ({ children, className }) => {
  return (
    <div className={className}>
      <main>
        {children}
      </main>
    </div>
  );
};
