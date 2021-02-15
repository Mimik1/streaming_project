print('Starting configuration');
db = new Mongo().getDB("api_dev_db");
db.createUser(
    {
        user: 'api_user',
        pwd: 'raspberry',
        roles: [{role: 'readWrite',db:'api_dev_db'}]
    }
);
db.createUser(
    {
        user: 'backend_user',
        pwd: 'papay',
        roles: [{role: 'readWrite',db:'api_dev_db'}]
    }
);
db.createUser(
    {
        user: 'analyser',
        pwd: 'banana',
        roles: [{role: 'readWrite',db:'api_dev_db'}]
    }
);

db.createCollection( 'photos',
    {
      autoIndexId: true,
      size: 4000000000,
      capped: true
    }
 );

 db.createCollection( 'labels_comments',
    {
      autoIndexId: true,
    }
 );
 db.createCollection( 'app_settings',
 { 
   autoIndexId: true,
 }
);

db.app_settings.insertOne({"url": "https://youtu.be/1EiC9bvVGnk","tag":"YT junction"});
