type CustomerPageProps = {
  params: {
    userId: string;
  };
};

export default function CustomerPage({ params }: CustomerPageProps) {
  return (
    <div className="page-card">
      <h1>Customer Profile</h1>
      <p className="muted">User ID: {params.userId}</p>
      <p className="muted">
        TODO: show customer 360 data, churn score, and recommendation widgets here.
      </p>
    </div>
  );
}
