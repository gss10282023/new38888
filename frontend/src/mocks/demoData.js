const isoDaysFromNow = (days) => {
  const date = new Date()
  date.setDate(date.getDate() + days)
  return date.toISOString()
}

export const DEMO_USERS = Object.freeze([
  {
    id: 1,
    name: 'William Nixon',
    email: 'admin@biotechfutures.demo',
    role: 'admin',
    track: 'Global',
    status: 'active',
    is_staff: true,
    profile: {
      firstName: 'William',
      lastName: 'Nixon',
      country: 'Australia',
      region: 'NSW',
      schoolName: '',
      yearLevel: null,
      availability: '',
      bio: 'Demo admin account (local-only).',
      areasOfInterest: ['Program Ops', 'Mentorship'],
      controlledInterests: ['AI & Data Science'],
      guardianEmail: '',
      supervisorEmail: '',
      joinPermissionGranted: true
    }
  },
  {
    id: 2,
    name: 'Anita Pickard',
    email: 'mentor@biotechfutures.demo',
    role: 'mentor',
    track: 'AUS-NSW',
    status: 'active',
    profile: {
      firstName: 'Anita',
      lastName: 'Pickard',
      country: 'Australia',
      region: 'NSW',
      schoolName: '',
      yearLevel: null,
      availability: 'Weeknights (6–8pm) and Sunday morning.',
      bio: 'Mentor demo account (local-only).',
      areasOfInterest: ['Biomedical Engineering'],
      controlledInterests: ['Biomedical Engineering'],
      guardianEmail: '',
      supervisorEmail: '',
      joinPermissionGranted: true
    }
  },
  {
    id: 3,
    name: 'Yilin Guo',
    email: 'student@biotechfutures.demo',
    role: 'student',
    track: 'AUS-NSW',
    status: 'active',
    profile: {
      firstName: 'Yilin',
      lastName: 'Guo',
      country: 'Australia',
      region: 'NSW',
      schoolName: 'Demo High School',
      yearLevel: 11,
      availability: 'After school weekdays.',
      bio: 'Student demo account (local-only).',
      areasOfInterest: ['Genomics & Precision Medicine'],
      controlledInterests: ['Genomics & Precision Medicine'],
      guardianEmail: 'guardian@biotechfutures.demo',
      supervisorEmail: 'supervisor@biotechfutures.demo',
      joinPermissionGranted: true
    }
  },
  {
    id: 4,
    name: 'Claudia Zhang',
    email: 'student2@biotechfutures.demo',
    role: 'student',
    track: 'AUS-NSW',
    status: 'active',
    profile: {
      firstName: 'Claudia',
      lastName: 'Zhang',
      country: 'Australia',
      region: 'NSW',
      schoolName: 'Demo High School',
      yearLevel: 12,
      availability: 'Saturday afternoon.',
      bio: 'Student demo account (local-only).',
      areasOfInterest: ['Medical Devices'],
      controlledInterests: ['Medical Devices'],
      guardianEmail: 'guardian2@biotechfutures.demo',
      supervisorEmail: 'supervisor@biotechfutures.demo',
      joinPermissionGranted: true
    }
  },
  {
    id: 5,
    name: 'Dr. Sophia Chen',
    email: 'supervisor@biotechfutures.demo',
    role: 'supervisor',
    track: 'AUS-NSW',
    status: 'active',
    profile: {
      firstName: 'Sophia',
      lastName: 'Chen',
      country: 'Australia',
      region: 'NSW',
      schoolName: '',
      yearLevel: null,
      availability: '',
      bio: 'Supervisor demo account (local-only).',
      areasOfInterest: ['Sustainability & Climate'],
      controlledInterests: ['Sustainability & Climate'],
      guardianEmail: '',
      supervisorEmail: '',
      joinPermissionGranted: true
    }
  }
])

export const getDemoUserByRole = (role) =>
  DEMO_USERS.find((user) => user.role === role) || DEMO_USERS[2]

export const createAccessToken = (userId) => `demo-access-${userId}`

export const createRefreshToken = (userId) => `demo-refresh-${userId}`

export const parseUserIdFromToken = (token) => {
  const raw = String(token || '')
  const match = raw.match(/^demo-(?:access|refresh)-(\d+)$/)
  if (!match) return null
  const id = Number(match[1])
  return Number.isFinite(id) ? id : null
}

export const createDemoState = () => {
  const mentors = DEMO_USERS.filter((u) => u.role === 'mentor')
  const mentor = mentors[0]

  const groupDetailA = {
    id: 'BTF046',
    name: 'BTF046',
    status: 'Schedule Event',
    track: 'AUS-NSW',
    mentor: mentor ? { id: mentor.id, name: mentor.name, email: mentor.email } : null,
    members: [
      { id: 3, name: DEMO_USERS[2].name, role: 'student', email: DEMO_USERS[2].email },
      { id: 4, name: DEMO_USERS[3].name, role: 'student', email: DEMO_USERS[3].email },
      { id: 5, name: DEMO_USERS[4].name, role: 'supervisor', email: DEMO_USERS[4].email }
    ],
    milestones: [
      {
        id: 101,
        title: 'Problem Discovery',
        description: 'Define the problem statement and success criteria.',
        order_index: 0,
        tasks: [
          { id: 1001, name: 'Confirm challenge theme', completed: true },
          { id: 1002, name: 'Draft stakeholder interview questions', completed: false },
          { id: 1003, name: 'Write a one-page problem brief', completed: false }
        ]
      },
      {
        id: 102,
        title: 'Prototype & Validation',
        description: 'Build a lightweight prototype and validate assumptions.',
        order_index: 1,
        tasks: [
          { id: 1004, name: 'Create prototype outline', completed: true },
          { id: 1005, name: 'Run 2 user tests', completed: false }
        ]
      }
    ]
  }

  const groupDetailB = {
    id: 'BTF001',
    name: 'BTF001',
    status: 'Mentor Matching',
    track: 'Global',
    mentor: mentor ? { id: mentor.id, name: mentor.name, email: mentor.email } : null,
    members: [
      { id: 3, name: DEMO_USERS[2].name, role: 'student', email: DEMO_USERS[2].email }
    ],
    milestones: [
      {
        id: 201,
        title: 'Kickoff',
        description: 'Align on timeline and deliverables.',
        order_index: 0,
        tasks: [
          { id: 2001, name: 'Introduce team members', completed: true },
          { id: 2002, name: 'Agree on weekly meeting cadence', completed: false }
        ]
      }
    ]
  }

  const groupsById = {
    [groupDetailA.id]: groupDetailA,
    [groupDetailB.id]: groupDetailB
  }

  const messagesByGroup = {
    [groupDetailA.id]: [
      {
        id: 5001,
        text: 'Welcome everyone! Please share your initial ideas.',
        timestamp: isoDaysFromNow(-3),
        author: { id: mentor?.id ?? 2, name: mentor?.name ?? 'Mentor' },
        attachments: [],
        moderation: { status: 'approved' }
      },
      {
        id: 5002,
        text: 'I’m interested in exploring low-cost diagnostics.',
        timestamp: isoDaysFromNow(-2),
        author: { id: 3, name: DEMO_USERS[2].name },
        attachments: [],
        moderation: { status: 'approved' }
      }
    ],
    [groupDetailB.id]: [
      {
        id: 5101,
        text: 'Kickoff agenda: introductions + milestones.',
        timestamp: isoDaysFromNow(-1),
        author: { id: mentor?.id ?? 2, name: mentor?.name ?? 'Mentor' },
        attachments: [],
        moderation: { status: 'approved' }
      }
    ]
  }

  const resources = [
    {
      id: 9001,
      title: 'Challenge Guidebook (Demo)',
      description: 'Overview of phases, timelines, and deliverables.',
      type: 'document',
      role: 'all',
      file_url: 'https://example.org/demo/guidebook.pdf',
      cover_image: null,
      download_count: 42,
      created_at: isoDaysFromNow(-20),
      updated_at: isoDaysFromNow(-2)
    },
    {
      id: 9002,
      title: 'Mentor Handbook (Demo)',
      description: 'Tips for mentoring student teams effectively.',
      type: 'document',
      role: 'mentor',
      file_url: 'https://example.org/demo/mentor-handbook.pdf',
      cover_image: null,
      download_count: 12,
      created_at: isoDaysFromNow(-18),
      updated_at: isoDaysFromNow(-3)
    },
    {
      id: 9003,
      title: 'Workshop Template Pack (Demo)',
      description: 'Reusable templates for ideation and user research.',
      type: 'template',
      role: 'student',
      file_url: 'https://example.org/demo/templates.zip',
      cover_image: null,
      download_count: 28,
      created_at: isoDaysFromNow(-15),
      updated_at: isoDaysFromNow(-5)
    }
  ]

  const events = [
    {
      id: 8001,
      title: 'Program Kickoff (Demo)',
      description: 'Welcome session and orientation.',
      long_description: 'Demo event used in UI previews.',
      date: isoDaysFromNow(5).slice(0, 10),
      time: '10:00 AM',
      location: 'Online',
      type: 'virtual',
      cover_image: null,
      register_link: 'https://example.org/demo/register',
      capacity: 200,
      created_at: isoDaysFromNow(-10),
      updated_at: isoDaysFromNow(-1),
      registration_count: 37,
      is_registered: false
    },
    {
      id: 8002,
      title: 'Mentor Training (Demo)',
      description: 'Mentor onboarding and best practices.',
      long_description: '',
      date: isoDaysFromNow(10).slice(0, 10),
      time: '2:00 PM',
      location: 'Online',
      type: 'virtual',
      cover_image: null,
      register_link: 'https://example.org/demo/mentor-training',
      capacity: 80,
      created_at: isoDaysFromNow(-9),
      updated_at: isoDaysFromNow(-2),
      registration_count: 12,
      is_registered: false
    }
  ]

  const announcements = [
    {
      id: 7001,
      title: 'Welcome to BIOTech Futures Hub (Demo)',
      summary: 'This is a demo announcement with mock content.',
      content: 'Explore Groups, Events, Resources, and the Admin Console in demo mode.',
      author: 'Program Team',
      audience: 'all',
      link: '',
      created_at: isoDaysFromNow(-7),
      updated_at: isoDaysFromNow(-7)
    },
    {
      id: 7002,
      title: 'Mentor Checklist Available (Demo)',
      summary: 'Mentors can review the onboarding checklist in the Resources page.',
      content: '',
      author: 'Mentor Coordination',
      audience: 'mentor',
      link: 'https://example.org/demo/mentor-checklist',
      created_at: isoDaysFromNow(-6),
      updated_at: isoDaysFromNow(-6)
    }
  ]

  return {
    users: DEMO_USERS.map((u) => ({ ...u, profile: { ...(u.profile || {}) } })),
    groupsById,
    messagesByGroup,
    resources,
    events,
    announcements,
    nextIds: {
      milestone: 3000,
      task: 4000,
      message: 6000,
      resource: 9100,
      event: 8100,
      announcement: 7100,
      user: 100,
      group: 10,
    }
  }
}
