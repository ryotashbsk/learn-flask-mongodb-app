db = db.getSiblingDB('sample_app');

db.items.createIndex({ name: 1 }, { unique: true });

db.items.insertMany([
  {
    name: 'Apple',
    description: 'Flask sample item from MongoDB',
    created_at: new Date('2026-01-01T00:00:00.000Z'),
  },
  {
    name: 'Banana',
    description: 'Data from MongoDB collection',
    created_at: new Date('2026-01-01T00:00:00.000Z'),
  },
]);
