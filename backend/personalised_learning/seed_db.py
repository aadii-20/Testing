from database import SessionLocal, engine
import models

models.Base.metadata.create_all(bind=engine)

def seed_db():
    db = SessionLocal()
    try:
        print("Checking database...")

        teacher_email = "t@g.com"
        existing_teacher = db.query(models.User).filter(models.User.email == teacher_email).first()
        
        if not existing_teacher:
            teacher = models.User(
                name="Prof. Sharma",
                email=teacher_email,
                password="123",
                role="teacher"
            )
            db.add(teacher)
            print(f"Added teacher: {teacher_email}")
        else:
            print(f"Teacher {teacher_email} already exists. Skipping...")

        students_list = [
            {"name": "Rahul", "email": "s@g.com", "acc": 75.0, "ch": 2, "cls": "10"},
            {"name": "Ananya", "email": "a@g.com", "acc": 42.5, "ch": 1, "cls": "10"},
            {"name": "Vikram", "email": "v@g.com", "acc": 92.0, "ch": 5, "cls": "11"},
            {"name": "Sanya", "email": "sanya@g.com", "acc": 58.0, "ch": 3, "cls": "12"}
        ]

        for s in students_list:
            existing_student = db.query(models.User).filter(models.User.email == s["email"]).first()
            
            if not existing_student:
                new_student = models.User(
                    name=s["name"],
                    email=s["email"],
                    password="123",
                    role="student",
                    class_level=s["cls"] 
                )
                db.add(new_student)
                db.flush()

                progress = models.Progress(
                    student_id=new_student.id,
                    accuracy=s["acc"],
                    chapters_completed=s["ch"]
                )
                db.add(progress)
                print(f"Added student: {s['email']}")
            else:
                print(f"Student {s['email']} already exists. Skipping...")

        db.commit()
        print("------------------------------------------")
        print("✅ Database Sync Complete!")
        print("------------------------------------------")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_db()