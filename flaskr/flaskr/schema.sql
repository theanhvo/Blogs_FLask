drop table if exists blogs;
create table blogs (
  id integer primary key autoincrement,
  title text not null,
  content text not null
);
